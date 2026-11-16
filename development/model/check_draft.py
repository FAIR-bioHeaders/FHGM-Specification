# SPDX-License-Identifier: MPL-2.0
"""Exercise the draft FHGM contract v0.1 checker against its fixtures.

Runs the acceptance and rejection matrix for the contract examples, the
committed model fixtures (regenerated and compared byte-for-byte) and the
S6k-derived record fixture. Also proves the demonstrated gap: files that the
released base schema and checksum accept while the model-level checker
rejects them. Requires fair-bioheaders and jsonschema. The model-conformance
workflow runs this matrix, and the manifest-driven runner in
``development/conformance/``, on every pull request and push to ``main``.

Since the dual-base decision of 2026-11-15 the matrix runs once per supplied
released FHGFF3 base (v0.5.0 and v0.6.0 bytes): every fixture keeps its verdict
under each base alone. With both bases supplied the checker's selection itself
is additionally exercised - each carrier must be routed to its declared release,
a superseded declaration judged by the oldest candidate that states it, and a
declaration no supplied base states refused with a selection error rather than
an enum accident.
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
CONFORMANCE_VECTORS = ROOT / "conformance" / "vectors"
S6K = ROOT / "examples" / "s6k"
FHGFF3_12_SCHEMA = "https://w3id.org/fair-bioheaders/fhgff3/v0.6.0"


def expect(base, file, error=None, predecessor=None, *extra_bases):
    """Run the checker over one file with one or more base-schema candidates.

    ``base`` may be a single path or a list of paths (each becomes one
    ``--base-schema`` argument); ``predecessor`` a path or list of paths.
    """
    bases = base if isinstance(base, list) else [base, *extra_bases]
    command = [sys.executable, str(VALIDATOR)]
    for one in bases:
        command += ["--base-schema", str(one)]
    if isinstance(predecessor, list):
        for path in predecessor:
            command.extend(["--predecessor", str(path)])
    elif predecessor:
        command.extend(["--predecessor", str(predecessor)])
    command.append(str(file))
    result = subprocess.run(command, capture_output=True, text=True)
    if error is None:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode == 1 and error in result.stderr, result
    return result


def twin_12(source, output, name):
    """Re-render a fixture under the released FHGFF3 1.2 identity.

    The two identity lines move and the checksum follows; records, pointers and
    feature bytes are the source's, exactly as the conformance matrix lane
    derives its twins.
    """
    metadata = parse_header(source.read_bytes().splitlines(keepends=True))
    del metadata["checksum"]
    metadata["schema"] = FHGFF3_12_SCHEMA
    metadata["schemaVersion"] = "1.2"
    # render() re-emits the ##gff-version directive itself; the payload is the
    # feature lines only (every FHGM fixture is plain, no embedded FASTA).
    payload = b"".join(
        line for line in source.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"#")
    )
    candidate = output / name
    candidate.write_bytes(render(metadata, payload))
    return candidate


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


def selection_checks(bases, output):
    """Base selection is exercised only when more than one release is supplied."""
    if len(bases) < 2:
        print("Single base supplied: selection cross-checks skipped "
              "(supply v0.5.0 and v0.6.0 bytes to run them).")
        return
    minimal = FIXTURES / "minimal.fhgff3.gff3"
    rich = FIXTURES / "rich.fhgff3.gff3"
    first, second = bases[0], bases[1]
    # A 1.1 carrier routes to the v0.5.0 bytes even when the 1.2 bytes are also
    # supplied, and a mixed chain (1.1 carrier naming a 1.1 predecessor with
    # both candidates available) resolves.
    routing = expect(first, rich, None, minimal, second)
    assert "schemaVersion '1.1' -> FAIR-bioHeaders/FAIR-bioHeaders-Specification@v0.5.0" \
        in routing.stdout, routing.stdout
    twin = twin_12(minimal, output, "twin-minimal.fhgff3.gff3")
    # A 1.2 carrier with a 1.1 predecessor under both candidates: each file is
    # judged by its own declared release.
    twin_rich = twin_12(rich, output, "twin-rich.fhgff3.gff3")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--base-schema", str(first),
         "--base-schema", str(second), "--predecessor", str(minimal),
         str(twin_rich)],
        capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "schemaVersion '1.2' -> FAIR-bioHeaders/FAIR-bioHeaders-Specification@v0.6.0" \
        in result.stdout, result.stdout
    assert "schemaVersion '1.1' -> FAIR-bioHeaders/FAIR-bioHeaders-Specification@v0.5.0" \
        in result.stdout, result.stdout
    # A superseded 1.0 carrier with both candidates is judged by the oldest
    # base that states 1.0 in its enum - the sealed v0.5.0 routing.
    carrier_10 = CONFORMANCE_VECTORS / "invalid" / "transport-1-0-extension.fhgff3.gff3"
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--base-schema", str(first),
         "--base-schema", str(second), str(carrier_10)],
        capture_output=True, text=True)
    assert result.returncode == 1, result
    assert "oldest supplied candidate" in result.stdout, result.stdout
    assert "'x-fhgm-models' should not be valid under" in result.stderr, result.stderr
    # A carrier declaring a version NO supplied base states at all is refused
    # with a selection error, not an enum accident. Construct one: the 1.2 twin
    # with its schemaVersion moved to 9.9.
    metadata = parse_header(twin.read_bytes().splitlines(keepends=True))
    del metadata["checksum"]
    metadata["schemaVersion"] = "9.9"
    future = output / "future-version.fhgff3.gff3"
    future_payload = b"".join(
        line for line in twin.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"#")
    )
    future.write_bytes(render(metadata, future_payload))
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--base-schema", str(first),
         "--base-schema", str(second), str(future)],
        capture_output=True, text=True)
    assert result.returncode == 1 and \
        "No supplied FHGFF3 base release states schemaVersion '9.9'" in result.stderr, \
        (result.stdout, result.stderr)
    # The same 9.9 carrier against a single-base harness refuses identically.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--base-schema", str(second), str(future)],
        capture_output=True, text=True)
    assert result.returncode == 1 and \
        "No supplied FHGFF3 base release states schemaVersion '9.9'" in result.stderr, \
        (result.stdout, result.stderr)
    print("Base selection checks passed: exact routing, oldest-stating fallback for "
          "superseded 1.0, and refusal of a version no supplied base states.")


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
    generated.mkdir(exist_ok=True)
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
    print(f"Draft FHGM contract v0.1 acceptance and rejection cases passed "
          f"against base {base.name}.")


if __name__ == "__main__":
    bases = [Path(argument) for argument in sys.argv[1:]]
    if not bases:
        raise SystemExit("usage: check_draft.py BASE [BASE ...]  "
                         "(released fhgff3.json bytes registered in base-schemas.json)")
    with TemporaryDirectory() as directory:
        output = Path(directory)
        for base in bases:
            run(base, output)
        selection_checks(bases, output)
