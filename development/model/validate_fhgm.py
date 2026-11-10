# SPDX-License-Identifier: MPL-2.0
"""Check the draft FHGM overlay on an FHGFF3 1.1 file."""

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
OVERLAY = Path(__file__).with_name("fhgm-draft.schema.json")
MODELS = "x-fhgm-models"


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


def validate_snapshot(data, base, overlay):
    lines = [
        header_text(line, b"#~")
        for kind, line in sequence_parts([data], b"#~", gff3=True)
        if kind is HEADER
    ]
    header = load_yaml("\n".join(lines))
    base.validate(header)
    overlay.validate(header)
    if checksum(BytesIO(data), "gff3") != header["checksum"]:
        raise ValueError("File checksum mismatch")

    targets = gene_targets(data)
    models = {}
    for model in header[MODELS]:
        model_id = model["modelId"]
        if model_id in models:
            raise ValueError(f"Duplicate model ID {model_id!r}")
        feature_id = model["featureId"]
        target_types = targets.get(feature_id.encode(), [])
        if len(target_types) != 1 or target_types[0] not in (b"gene", b"SO:0000704"):
            raise ValueError(f"Model {model_id!r} must target one local gene row: {feature_id!r}")
        models[model_id] = model
    return header, models


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


def validate_revisions(header, models, predecessors):
    current_keys = assembly_keys(header)
    for model_id, model in models.items():
        if "predecessor" not in model:
            continue
        pointer = model["predecessor"]
        target_checksum = pointer["annotationChecksum"]
        if target_checksum == header["checksum"] or target_checksum not in predecessors:
            raise ValueError(f"Model {model_id!r} requires a distinct predecessor snapshot")
        prior_header, prior_models = predecessors[target_checksum]
        prior = prior_models.get(model_id)
        if (
            pointer["modelId"] != model_id
            or prior is None
            or prior["modelVersion"] != pointer["modelVersion"]
            or prior["modelVersion"] == model["modelVersion"]
        ):
            raise ValueError(f"Model {model_id!r} has an invalid predecessor identity or version")
        prior_keys = assembly_keys(prior_header)
        shared = current_keys.keys() & prior_keys.keys()
        if not shared or any(current_keys[key] != prior_keys[key] for key in shared):
            raise ValueError(f"Model {model_id!r} lacks a matching predecessor assembly link")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-schema", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, action="append", default=[])
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    try:
        base = load_base(args.base_schema)
        overlay = Draft202012Validator(json.loads(OVERLAY.read_bytes()))
        header, models = validate_snapshot(args.file.read_bytes(), base, overlay)
        predecessors = {}
        for path in args.predecessor:
            snapshot = validate_snapshot(path.read_bytes(), base, overlay)
            predecessors[snapshot[0]["checksum"]] = snapshot
        validate_revisions(header, models, predecessors)
    except ValidationError as exc:
        parser.exit(1, f"{exc.json_path}: {exc.message}\n")
    except (OSError, ValueError, YAMLError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Passed FHGFF3 header, checksum and draft FHGM checks for {len(models)} model(s).")


if __name__ == "__main__":
    main()
