# SPDX-License-Identifier: MPL-2.0
"""Exercise the draft FHGM contract v0.1 checker against its fixtures.

Runs the acceptance and rejection matrix for the contract examples, the
committed model fixtures (regenerated and compared byte-for-byte) and the
S6k-derived record fixture. Also proves the demonstrated gap: files that the
released base schema and checksum accept while the model-level checker
rejects them. Requires fair-bioheaders and jsonschema; not part of CI.
"""

import copy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "revision"))
from check_revision import feature_payload, parse_header, render, validate_file

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "model" / "validate_fhgm.py"
FIXTURES = ROOT / "examples" / "contract"
MODEL_FIXTURES = ROOT / "examples" / "model"
S6K = ROOT / "examples" / "s6k"


def expect(base, file, error=None, predecessor=None):
    command = [sys.executable, str(VALIDATOR), "--base-schema", str(base), str(file)]
    if isinstance(predecessor, list):
        for path in predecessor:
            command.extend(["--predecessor", str(path)])
    elif predecessor:
        command.extend(["--predecessor", str(predecessor)])
    result = subprocess.run(command, capture_output=True, text=True)
    if error is None:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode == 1 and error in result.stderr, result


def contract_examples(base, output):
    minimal = FIXTURES / "minimal.fhgff3.gff3"
    rich = FIXTURES / "rich.fhgff3.gff3"
    expect(base, minimal)
    expect(base, rich, predecessor=minimal)
    expect(base, rich, "predecessor snapshot is the current file or was not supplied")

    pilot = ROOT / "examples" / "revision" / "check_revision.py"
    subprocess.run([sys.executable, str(pilot), str(base), str(output)], check=True)
    original = output / "original.gff3"
    expect(base, original)
    expect(base, output / "revised.gff3", predecessor=original)
    expect(base, output / "wrong-model.gff3", "predecessor is unresolvable", original)
    expect(base, output / "stale-predecessor.gff3", "predecessor is unresolvable", original)

    metadata = parse_header(minimal.read_bytes().splitlines(keepends=True))
    del metadata["checksum"]
    models = metadata["x-fhgm-models"]
    payload = feature_payload(30)
    for feature_id, rows, error in (
        ("missing", payload, "must target one local gene"),
        ("toy-a-rna", payload, "must target one local gene"),
        ("toy-a", payload + payload, "must target one local gene"),
        ("toy-a", payload.replace(b"ID=toy-a\n", b"ID=toy%2Da\n"), None),
    ):
        models[0]["featureId"] = feature_id
        candidate = output / "target.gff3"
        candidate.write_bytes(render(metadata, rows))
        expect(base, candidate, error)

    invalid_fields = (
        ("contributors", [{"name": "Example", "role": "curator", "uri": 42}]),
        ("evidence", [{"description": "Synthetic evidence", "uri": 42}]),
        ("methods", {"software": [{"name": "Synthetic software", "uri": 42}]}),
        ("methods", {"protocol": 42}),
        ("publication", {"article": None}),
        ("evidence", [{"description": "Synthetic evidence", "uri": "not a URI"}]),
        ("methods", {"protocol": "not a URI"}),
    )
    for field, value in invalid_fields:
        invalid_metadata = copy.deepcopy(metadata)
        invalid_metadata["x-fhgm-models"][0][field] = value
        candidate.write_bytes(render(invalid_metadata, payload))
        expect(base, candidate, "invalid under draft contract v0.1")

    models.append(dict(models[0]))
    candidate.write_bytes(render(metadata, payload))
    expect(base, candidate, "Ambiguous model ID")
    models.pop()

    reference = metadata.pop("genomeReference")
    candidate.write_bytes(render(metadata, payload))
    expect(base, candidate, "is not valid under any")
    metadata["genomeReference"] = dict(reference, accession="SYNTHETIC_OTHER.1")

    revised = parse_header(rich.read_bytes().splitlines(keepends=True))
    del revised["checksum"]
    revised["genomeReference"] = metadata["genomeReference"]
    revised["x-fhgm-models"][0]["reference"]["genomeReference"] = metadata["genomeReference"]
    candidate.write_bytes(render(revised, payload))
    expect(base, candidate, "no matching assembly link", minimal)

    candidate.write_bytes(minimal.read_bytes() + b"# changed bytes\n")
    expect(base, candidate, "File checksum mismatch")


def s6k_fixture(base):
    derived = S6K / "DanaCAF1_S6k.fhgm-models.fhgff3.gff3"
    plain = S6K / "DanaCAF1_S6k.gff3"
    kept = b"".join(
        line for line in derived.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"#~")
    )
    assert kept == plain.read_bytes(), "S6k feature payload bytes drifted"
    expect(base, derived)


def model_fixtures(base, output):
    generated = output / "regenerated"
    generated.mkdir()
    subprocess.run(
        [sys.executable, str(MODEL_FIXTURES / "make_fixtures.py"), str(generated)],
        check=True, capture_output=True,
    )
    for fixture in sorted(MODEL_FIXTURES.glob("*.fhgff3.gff3")):
        assert (generated / fixture.name).read_bytes() == fixture.read_bytes(), \
            f"{fixture.name} is not byte-reproducible"

    v1 = MODEL_FIXTURES / "snapshot-v1.fhgff3.gff3"
    v2 = MODEL_FIXTURES / "snapshot-v2.fhgff3.gff3"
    predecessor_name_mismatch = MODEL_FIXTURES / "predecessor-name-mismatch.fhgff3.gff3"
    expect(base, MODEL_FIXTURES / "valid-single.fhgff3.gff3")
    expect(base, v1)
    expect(base, v2, predecessor=v1)
    expect(base, v2, predecessor=[v1, predecessor_name_mismatch])
    expect(base, MODEL_FIXTURES / "pointer-absent-snapshot.fhgff3.gff3",
           "predecessor is unresolvable", v1)
    expect(base, MODEL_FIXTURES / "ambiguous-model-id.fhgff3.gff3", "Ambiguous model ID")
    expect(base, MODEL_FIXTURES / "version-reuse.fhgff3.gff3",
           "reuses the predecessor model version", v1)
    expect(base, MODEL_FIXTURES / "pointer-version-mismatch.fhgff3.gff3",
           "predecessor records version", v1)
    expect(base, MODEL_FIXTURES / "predecessor-name-mismatch.fhgff3.gff3",
           "names another model ID", v1)
    expect(base, MODEL_FIXTURES / "version-gap-skip.fhgff3.gff3",
           "already has a recorded successor", [v1, v2])
    expect(base, MODEL_FIXTURES / "record-without-reference.fhgff3.gff3",
           "invalid under draft contract v0.1")
    expect(base, MODEL_FIXTURES / "record-reference-conflict.fhgff3.gff3",
           "contradicts the file genome link")

    # The demonstrated gap: the released base schema and checksum accept every
    # rejection fixture, and only the model-level checker rejects them.
    validator = None
    for fixture in sorted(MODEL_FIXTURES.glob("*.fhgff3.gff3")):
        if fixture.name.startswith(("valid-", "snapshot-")):
            continue
        data = fixture.read_bytes()
        if validator is None:
            import json

            from jsonschema import Draft202012Validator

            validator = Draft202012Validator(
                json.loads(base.read_bytes()),
                format_checker=Draft202012Validator.FORMAT_CHECKER,
            )
        validate_file(data, validator)
    print("Base schema and checksum accept every rejection fixture.")


def run(base, output):
    contract_examples(base, output)
    s6k_fixture(base)
    model_fixtures(base, output)
    print("Draft FHGM contract v0.1 acceptance and rejection cases passed.")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        run(Path(sys.argv[1]), Path(directory))
