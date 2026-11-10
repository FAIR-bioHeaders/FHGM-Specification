"""Generate and check synthetic FHGFF3 revision cases against a supplied schema."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA = "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0"
DIRECTIVE = b"##gff-version 3\n"
REVISION = "x-fhgm-supersedes"


def sha512t24u(data):
    return base64.urlsafe_b64encode(hashlib.sha512(data).digest()[:24]).decode()


def canonical(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def synthetic_reference():
    # One synthetic FASTA record, >toy followed by 100 uppercase A bases.
    attributes = {"names": ["toy"], "sequences": ["SQ." + sha512t24u(b"A" * 100)]}
    level_one = {key: sha512t24u(canonical(value)) for key, value in attributes.items()}
    return {"accession": "SYNTHETIC_ASSEMBLY.1", "seqcol_id": sha512t24u(canonical(level_one))}


def checksum(content):
    return base64.b64encode(hashlib.new("sha512_256", content).digest()).decode()


def feature_payload(end):
    return (
        f"toy\tpilot\tgene\t10\t{end}\t.\t+\t.\tID=toy-gene\n"
        f"toy\tpilot\tlncRNA\t10\t{end}\t.\t+\t.\tID=toy-rna;Parent=toy-gene\n"
        f"toy\tpilot\texon\t10\t{end}\t.\t+\t.\tParent=toy-rna\n"
    ).encode()


def render(metadata, payload):
    header = b"".join(
        f"#~{key}: ".encode() + canonical(value) + b"\n"
        for key, value in metadata.items()
    )
    value = checksum(DIRECTIVE + header + payload)
    return DIRECTIVE + header + f"#~checksum: {value}\n".encode() + payload


def parse_header(lines):
    return yaml.safe_load(b"".join(line[2:] for line in lines if line.startswith(b"#~")))


def validate_file(data, validator):
    lines = data.splitlines(keepends=True)
    header = parse_header(lines)
    validator.validate(header)
    covered = b"".join(line for line in lines if not line.startswith(b"#~checksum:"))
    if checksum(covered) != header["checksum"]:
        raise ValueError("File checksum mismatch")
    return header


def predecessor_matches(successor, predecessor):
    """Resolve a fixture's explicit file pointer, independent of adoption."""
    target = successor[REVISION]
    return (
        target["predecessorChecksum"] == predecessor["checksum"]
        and target["predecessorVersion"] == predecessor["version"]
        and successor["genomeReference"] == predecessor["genomeReference"]
    )


def run(schema_path, output):
    validator = Draft202012Validator(
        json.loads(schema_path.read_bytes()), format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    common = {
        "schema": SCHEMA,
        "schemaVersion": "1.1",
        "annotation": "Synthetic noncoding locus for the FHGM revision pilot",
        "taxon": {"name": "Synthetic example"},
        "metadataAuthor": [{"name": "OpenAI Codex"}],
        "dateCreated": "2026-11-10",
        "genomeReference": synthetic_reference(),
    }
    original_bytes = render(dict(common, version="1"), feature_payload(30))
    original = validate_file(original_bytes, validator)
    target = {"predecessorVersion": "1", "predecessorChecksum": original["checksum"]}
    revised_metadata = dict(common, version="2", **{REVISION: target})
    revised_bytes = render(revised_metadata, feature_payload(35))
    revised = validate_file(revised_bytes, validator)
    if not predecessor_matches(revised, original):
        raise ValueError("The revision must resolve to the original file")

    stale_target = dict(target, predecessorChecksum=checksum(b"unrelated fixture bytes"))
    stale_bytes = render(dict(revised_metadata, **{REVISION: stale_target}), feature_payload(35))
    stale = validate_file(stale_bytes, validator)
    if predecessor_matches(stale, original):
        raise ValueError("A stale predecessor pointer must fail resolution")

    # Try the same relationship as a standard derivedFrom term.
    unsupported = dict(
        common,
        version="2",
        derivedFrom=[
            {"headerType": "FHGFF3", "relationship": "supersedes", "checksum": original["checksum"]}
        ],
    )
    unsupported_bytes = render(unsupported, feature_payload(35))
    unsupported_header = parse_header(unsupported_bytes.splitlines(keepends=True))
    errors = list(validator.iter_errors(unsupported_header))
    if len(errors) != 1 or list(errors[0].absolute_path) != ["derivedFrom", 0, "relationship"]:
        raise ValueError("Expected the base schema to reject the supersedes term")

    for name, data in (
        ("original.gff3", original_bytes),
        ("revised.gff3", revised_bytes),
        ("stale-predecessor.gff3", stale_bytes),
    ):
        (output / name).write_bytes(data)
    print("Original and revision pass schema and checksum checks; predecessor resolves.")
    print("Stale predecessor passes schema and checksum checks; predecessor does not resolve.")
    print("Base schema rejects derivedFrom.relationship=supersedes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    parser.add_argument("output", type=Path, help="Existing directory for generated fixtures")
    args = parser.parse_args()
    run(args.schema, args.output)
