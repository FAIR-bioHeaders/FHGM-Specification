# SPDX-License-Identifier: MPL-2.0
"""Model-level checker for the draft FHGM contract v0.1 on an FHGFF3 1.1 file.

Runs three passes over an explicit selection: the released FHGFF3 1.1 base
schema (transport and file identity only), the draft transport overlay
(fhgm-draft.schema.json) and the native record contract
(fhgm-model.schema.json) per embedded record. Pointer resolution then reports
one verdict per revision claim: resolvable, unresolvable or ambiguous. A
resolvable pointer only identifies a predecessor record; curator acceptance is
never asserted here.
"""

import argparse
from collections import defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import unquote_to_bytes

from bioheaders import HEADER, header_text, load_yaml, sequence_parts
from bioheaders.cli import checksum
from jsonschema import Draft202012Validator, ValidationError
from yaml import YAMLError

BASE_SHA256 = "20ce320f5d706f11ed21cdece4dfb56e3568b50be126e25b4016f46f2e8e416c"
TRANSPORT = Path(__file__).with_name("fhgm-draft.schema.json")
MODEL_CONTRACT = Path(__file__).with_name("fhgm-model.schema.json")
MODELS = "x-fhgm-models"
RESOLVABLE = "resolvable"
UNRESOLVABLE = "unresolvable"
AMBIGUOUS = "ambiguous"


class ModelCheckError(ValueError):
    """A draft FHGM model-level rule failed; the reason is the message."""


def load_base(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != BASE_SHA256:
        raise ValueError("Expected the released v0.5.0 fhgff3.json bytes")
    return Draft202012Validator(json.loads(data), format_checker=Draft202012Validator.FORMAT_CHECKER)


def gene_targets(data):
    targets = defaultdict(list)
    for line in data.splitlines():
        if line == b"##FASTA":
            break
        if not line.strip() or line.startswith(b"#"):
            continue
        columns = line.split(b"\t")
        if len(columns) != 9:
            raise ValueError("Expected nine columns in each GFF3 feature row")
        for attribute in columns[8].split(b";"):
            key, _, value = attribute.partition(b"=")
            if key == b"ID":
                targets[unquote_to_bytes(value)].append(columns[2])
    return targets


def assembly_keys(header):
    keys = {}
    if "genomeReference" in header:
        reference = header["genomeReference"]
        keys["accession"] = reference["accession"]
        keys["seqcol_id"] = reference["seqcol_id"]
    for parent in header.get("derivedFrom", []):
        if parent["headerType"] == "FHR" and parent["relationship"] == "annotates":
            keys["fhr_checksum"] = parent["checksum"]
    return keys


def reference_keys(model):
    keys = {}
    reference = model.get("reference", {})
    if "genomeReference" in reference:
        keys["accession"] = reference["genomeReference"]["accession"]
        keys["seqcol_id"] = reference["genomeReference"]["seqcol_id"]
    if "annotates" in reference:
        keys["fhr_checksum"] = reference["annotates"]
    return keys


def links_conflict(left, right):
    return any(left[key] != right[key] for key in left.keys() & right.keys())


def links_match(left, right):
    return bool(left.keys() & right.keys()) and not links_conflict(left, right)


def validate_snapshot(data, base, transport, record_contract):
    lines = [
        header_text(line, b"#~")
        for kind, line in sequence_parts([data], b"#~", gff3=True)
        if kind is HEADER
    ]
    header = load_yaml("\n".join(lines))
    base.validate(header)
    transport.validate(header)
    if checksum(BytesIO(data), "gff3") != header["checksum"]:
        raise ValueError("File checksum mismatch")

    targets = gene_targets(data)
    models = defaultdict(list)
    file_keys = assembly_keys(header)
    for index, model in enumerate(header[MODELS]):
        try:
            record_contract.validate(model)
        except ValidationError as exc:
            raise ModelCheckError(
                f"Model record {index} is invalid under draft contract v0.1: "
                f"{exc.json_path}: {exc.message}"
            ) from exc
        model_id = model["modelId"]
        if model_id not in models:
            feature_id = model["featureId"]
            target_types = targets.get(feature_id.encode(), [])
            if len(target_types) != 1 or target_types[0] not in (b"gene", b"SO:0000704"):
                raise ModelCheckError(
                    f"Model {model_id!r} must target one local gene row: {feature_id!r}"
                )
        models[model_id].append(model)
        record_keys = reference_keys(model)
        if links_conflict(record_keys, file_keys):
            raise ModelCheckError(
                f"Model {model_id!r} carries a reference that contradicts the file genome link"
            )
        if not links_match(record_keys, file_keys):
            raise ModelCheckError(
                f"Model {model_id!r} has no reference form comparable with the file genome link"
            )
    for model_id, records in models.items():
        if len(records) > 1:
            raise ModelCheckError(
                f"Ambiguous model ID {model_id!r}: {len(records)} records share it in one snapshot"
            )
    return header, {model_id: records[0] for model_id, records in models.items()}


def resolve_predecessor(model_id, model, header, predecessors):
    """Return (verdict, detail) for one revision pointer. Never raises."""
    pointer = model["predecessor"]
    snapshot = pointer["annotationChecksum"]
    if snapshot == header["checksum"] or snapshot not in predecessors:
        return UNRESOLVABLE, "the predecessor snapshot is the current file or was not supplied"
    if pointer["modelId"] != model_id:
        return UNRESOLVABLE, f"the pointer names another model ID {pointer['modelId']!r}"
    prior_header, prior_models = predecessors[snapshot]
    prior = prior_models.get(model_id)
    if prior is None:
        return UNRESOLVABLE, f"the predecessor snapshot has no model {model_id!r}"
    if prior["modelVersion"] != pointer["modelVersion"]:
        return UNRESOLVABLE, (
            f"the predecessor records version {prior['modelVersion']!r}, "
            f"not {pointer['modelVersion']!r}"
        )
    if prior["modelVersion"] == model["modelVersion"]:
        return UNRESOLVABLE, "the revision reuses the predecessor model version"
    for other_checksum, (other_header, other_models) in predecessors.items():
        if other_checksum == snapshot:
            continue
        other = other_models.get(model_id)
        other_pointer = other.get("predecessor") if other else None
        if (
            other_pointer
            and other_pointer["annotationChecksum"] == snapshot
            and other_pointer["modelVersion"] == pointer["modelVersion"]
        ):
            return UNRESOLVABLE, (
                "the pointed record already has a recorded successor "
                f"in supplied snapshot {other_checksum[:8]}..."
            )
    if not links_match(assembly_keys(header), assembly_keys(prior_header)):
        return UNRESOLVABLE, "no matching assembly link with the predecessor snapshot"
    if not links_match(reference_keys(model), reference_keys(prior)):
        return UNRESOLVABLE, "no matching record reference with the predecessor record"
    return RESOLVABLE, f"predecessor {snapshot[:8]}... version {pointer['modelVersion']!r}"


def validate_revisions(header, models, predecessors):
    for model_id, model in models.items():
        if "predecessor" not in model:
            print(f"model {model_id} version {model['modelVersion']!r}: no predecessor claim")
            continue
        verdict, detail = resolve_predecessor(model_id, model, header, predecessors)
        if verdict != RESOLVABLE:
            raise ModelCheckError(
                f"Model {model_id!r} predecessor is {verdict}: {detail}"
            )
        print(f"model {model_id} version {model['modelVersion']!r}: {verdict} ({detail})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-schema", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, action="append", default=[])
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    try:
        base = load_base(args.base_schema)
        transport = Draft202012Validator(json.loads(TRANSPORT.read_bytes()))
        record_contract = Draft202012Validator(json.loads(MODEL_CONTRACT.read_bytes()))
        header, models = validate_snapshot(args.file.read_bytes(), base, transport, record_contract)
        predecessors = {}
        for path in args.predecessor:
            snapshot = validate_snapshot(path.read_bytes(), base, transport, record_contract)
            predecessors[snapshot[0]["checksum"]] = snapshot
        validate_revisions(header, models, predecessors)
    except ValidationError as exc:
        parser.exit(1, f"{exc.json_path}: {exc.message}\n")
    except (OSError, ValueError, YAMLError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Passed FHGFF3 header, checksum and draft FHGM checks for {len(models)} model(s).")


if __name__ == "__main__":
    main()
