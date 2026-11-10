# SPDX-License-Identifier: MPL-2.0
"""Exercise the draft validator against existing and derived fixtures."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "revision"))
from check_revision import feature_payload, parse_header, render

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "model" / "validate_fhgm.py"
FIXTURES = ROOT / "examples" / "contract"


def expect(base, file, error=None, predecessor=None):
    command = [sys.executable, str(VALIDATOR), "--base-schema", str(base), str(file)]
    if predecessor:
        command.extend(["--predecessor", str(predecessor)])
    result = subprocess.run(command, capture_output=True, text=True)
    if error is None:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode == 1 and error in result.stderr, result


def run(base, output):
    minimal = FIXTURES / "minimal.fhgff3.gff3"
    rich = FIXTURES / "rich.fhgff3.gff3"
    expect(base, minimal)
    expect(base, rich, predecessor=minimal)
    expect(base, rich, "requires a distinct predecessor snapshot")

    pilot = ROOT / "examples" / "revision" / "check_revision.py"
    subprocess.run([sys.executable, str(pilot), str(base), str(output)], check=True)
    original = output / "original.gff3"
    expect(base, original)
    expect(base, output / "revised.gff3", predecessor=original)
    expect(base, output / "wrong-model.gff3", "invalid predecessor identity", original)
    expect(base, output / "stale-predecessor.gff3", "requires a distinct predecessor", original)

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

    models.append(dict(models[0]))
    candidate.write_bytes(render(metadata, payload))
    expect(base, candidate, "Duplicate model ID")
    models.pop()

    reference = metadata.pop("genomeReference")
    candidate.write_bytes(render(metadata, payload))
    expect(base, candidate, "is not valid under any")
    metadata["genomeReference"] = dict(reference, accession="SYNTHETIC_OTHER.1")

    revised = parse_header(rich.read_bytes().splitlines(keepends=True))
    del revised["checksum"]
    revised["genomeReference"] = metadata["genomeReference"]
    candidate.write_bytes(render(revised, payload))
    expect(base, candidate, "lacks a matching predecessor assembly link", minimal)

    candidate.write_bytes(minimal.read_bytes() + b"# changed bytes\n")
    expect(base, candidate, "File checksum mismatch")
    print("Draft FHGM acceptance and rejection cases passed.")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        run(Path(sys.argv[1]), Path(directory))
