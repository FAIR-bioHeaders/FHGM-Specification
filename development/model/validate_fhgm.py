# SPDX-License-Identifier: MPL-2.0
"""Model-level checker for the draft FHGM contract v0.1 on FHGFF3 1.1/1.2 files.

Runs three passes over an explicit selection: the released FHGFF3 base schema
(transport and file identity only), the draft transport overlay
(fhgm-draft.schema.json) and the native record contract (fhgm-model.schema.json)
per embedded record. Base selection, not base substitution: each loaded file
declares a released FHGFF3 identity through its schemaVersion, and the checker
validates it against the registered bytes of THAT release
(base-schemas.json), refusing any file whose declared version no supplied base
states. The selected base is printed for every loaded file, so each verdict
carries the release bytes that produced it. Pointer resolution then reports one
verdict per revision claim: resolvable, unresolvable or ambiguous. A resolvable
pointer only identifies a predecessor record; curator acceptance is never
asserted here. FHGM itself is a draft: it has no schemaVersion, no schema URL,
no registry row and no release form (selection rule V7).
"""

import argparse
from collections import defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import unquote_to_bytes, urlsplit

from bioheaders import HEADER, header_text, load_yaml, sequence_parts
from bioheaders.cli import checksum
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from yaml import YAMLError

BASE_REGISTRY = Path(__file__).with_name("base-schemas.json")
TRANSPORT = Path(__file__).with_name("fhgm-draft.schema.json")
MODEL_CONTRACT = Path(__file__).with_name("fhgm-model.schema.json")
MODELS = "x-fhgm-models"
RESOLVABLE = "resolvable"
UNRESOLVABLE = "unresolvable"
AMBIGUOUS = "ambiguous"

FORMAT_CHECKER = Draft202012Validator.FORMAT_CHECKER
if "uri" not in FORMAT_CHECKER.checkers:
    FORMAT_CHECKER = FormatChecker()

    @FORMAT_CHECKER.checks("uri")
    def is_uri(value):
        if not isinstance(value, str):
            return True
        if (
            re.search(r"\s", value)
            or re.search(r"%(?![0-9A-Fa-f]{2})", value)
            or any(ord(char) < 0x21 or ord(char) > 0x7E or char in '<>"{}|\\^`' for char in value)
        ):
            return False
        try:
            parts = urlsplit(value)
        except ValueError:
            return False
        return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", parts.scheme))


class ModelCheckError(ValueError):
    """A draft FHGM model-level rule failed; the reason is the message."""


def _version_key(version):
    return tuple(int(part) for part in version.split("."))


def load_registry():
    """The registered FHGFF3 base releases, keyed by their exact-byte digest."""
    document = json.loads(BASE_REGISTRY.read_bytes())
    return {record["sha256"]: record for record in document["bases"]}


def load_bases(paths):
    """Resolve each supplied --base-schema file against the registry.

    Returns (digest, record, validator) triples oldest release first. Unknown
    bytes are refused: a checker run must say which registered release it
    evaluated.
    """
    registry = load_registry()
    candidates = []
    for path in paths:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        record = registry.get(digest)
        if record is None:
            raise ValueError(
                f"{path}: sha256 {digest} is not a registered FHGFF3 base release; "
                f"{BASE_REGISTRY.name} registers "
                f"{', '.join(sorted({r['schemaVersion'] for r in registry.values()}))}")
        candidates.append((digest, record, Draft202012Validator(
            json.loads(data), format_checker=Draft202012Validator.FORMAT_CHECKER)))
    candidates.sort(key=lambda triple: _version_key(triple[1]["schemaVersion"]))
    return candidates


def choose_base(declared, candidates):
    """Pick the candidate that validates a carrier declaring `declared`.

    Returns (digest, record, validator, basis). Exact version match first; a
    declared version with no base of its own among the candidates (a superseded
    version such as 1.0) is judged by the oldest candidate whose enum states it,
    because the R15 extension floor rides on that clause; a version no candidate
    states at all is refused rather than evaluated against bytes the carrier
    never cited.
    """
    if isinstance(declared, str) and re.fullmatch(r"[0-9]+\.[0-9]+", declared):
        for digest, record, validator in candidates:
            if record["schemaVersion"] == declared:
                return (digest, record, validator,
                        "exact match on the declared schemaVersion")
        for digest, record, validator in candidates:
            if declared in record["acceptsSchemaVersions"]:
                return digest, record, validator, (
                    f"no supplied base states {declared!r} as its own release; the "
                    f"oldest supplied candidate whose enum includes it")
        raise ValueError(
            f"No supplied FHGFF3 base release states schemaVersion {declared!r}; "
            "supply the release the carrier cites (see base-schemas.json)")
    digest, record, validator = candidates[0]
    return digest, record, validator, (
        "carrier declares no usable schemaVersion string; probed with the oldest "
        "supplied base, whose requiredness report is the verdict")


def describe(record, digest):
    return (f"{record['repository']}@{record['ref']} {record['path']} "
            f"(sha256 {digest[:16]}...)")


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


def parse_snapshot(data):
    """The header document of a snapshot's exact bytes, before any validation."""
    lines = [
        header_text(line, b"#~")
        for kind, line in sequence_parts([data], b"#~", gff3=True)
        if kind is HEADER
    ]
    return load_yaml("\n".join(lines))


def validate_snapshot(data, candidates, transport, record_contract, label="carrier"):
    header = parse_snapshot(data)
    if not isinstance(header, dict):
        raise ValueError("FHGFF3 header metadata must be an object")
    digest, record, base, basis = choose_base(header.get("schemaVersion"), candidates)
    print(f"Base selection: {label} declares schemaVersion "
          f"{header.get('schemaVersion')!r} -> {describe(record, digest)} ({basis})")
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
            and other_pointer["modelId"] == model_id
            and other_pointer["modelVersion"] == pointer["modelVersion"]
            and other["modelVersion"] != prior["modelVersion"]
            and links_match(assembly_keys(other_header), assembly_keys(prior_header))
            and links_match(reference_keys(other), reference_keys(prior))
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
    parser.add_argument("--base-schema", type=Path, action="append", required=True,
                        help="bytes of a released fhgff3.json named in base-schemas.json; "
                             "repeat to hand the checker more than one base release")
    parser.add_argument("--predecessor", type=Path, action="append", default=[])
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    try:
        candidates = load_bases(args.base_schema)
        transport = Draft202012Validator(json.loads(TRANSPORT.read_bytes()))
        record_contract = Draft202012Validator(
            json.loads(MODEL_CONTRACT.read_bytes()),
            format_checker=FORMAT_CHECKER,
        )
        header, models = validate_snapshot(
            args.file.read_bytes(), candidates, transport, record_contract)
        predecessors = {}
        for path in args.predecessor:
            snapshot = validate_snapshot(
                path.read_bytes(), candidates, transport, record_contract,
                label=f"predecessor {path.name}")
            predecessors[snapshot[0]["checksum"]] = snapshot
        validate_revisions(header, models, predecessors)
    except ValidationError as exc:
        parser.exit(1, f"{exc.json_path}: {exc.message}\n")
    except (OSError, ValueError, YAMLError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Passed FHGFF3 header, checksum and draft FHGM checks for {len(models)} model(s).")


if __name__ == "__main__":
    main()
