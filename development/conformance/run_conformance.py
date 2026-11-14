# SPDX-License-Identifier: MPL-2.0
"""Independent runner for the draft FHGM conformance manifest.

An FHGM model record cannot be tested by schema vectors alone: every model-level
rejection in this suite passes the released FHGFF3 1.1 base schema and its
exact-byte checksum (that gap is why the separate checker exists, and the
manifest records it per vector). This script therefore reports the layers
**separately**, as FHGM #9 requires:

    base     the released fhgff3.json schema alone, over the parsed header
    checksum the file-bound SHA-512/256 of the exact bytes, recomputed here with
             hashlib over every byte except the root checksum line and its
             terminator - deliberately a second implementation next to the
             toolkit's, so a shared bug cannot hide
    gff3     ``gff3-validate --no-header``, when that separate tool is installed
    model    ``development/model/validate_fhgm.py``: transport overlay, native
             record contract and the model-level rules with the pointer verdicts

Nothing is imported from ``check_draft.py`` or from the generators. Vector
outcomes are only ever read from a run of the committed checker:
``make_vectors.py`` states no expectations, and ``--seal`` records digests and
checksums from bytes that already matched a recorded outcome.

Exit status: 0 when every vector matched what the manifest records, 1 on a
mismatch, 2 when the suite itself cannot run (missing base schema, unreadable
manifest). Skipped lanes are printed, never hidden.

    python3 run_conformance.py --base-schema /path/to/fhgff3-v0.5.0.json
    python3 run_conformance.py --offline              # bytes, digests, checksums
    python3 run_conformance.py --base-schema ... --verbose
    python3 run_conformance.py --base-schema ... --seal   # re-record digests
"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE.parent
REPO = DEVELOPMENT.parent
MANIFEST = HERE / "manifest.json"
CHECKER = DEVELOPMENT / "model" / "validate_fhgm.py"
GENERATORS = {
    "make_fixtures": DEVELOPMENT / "examples" / "model" / "make_fixtures.py",
    "make_vectors": HERE / "make_vectors.py",
}
S6K_PROFILE = DEVELOPMENT / "examples" / "s6k" / "DanaCAF1_S6k.fhgff3.gff3"
S6K_DERIVED = DEVELOPMENT / "examples" / "s6k" / "DanaCAF1_S6k.fhgm-models.fhgff3.gff3"
EMBED = DEVELOPMENT / "examples" / "s6k" / "embed_models.py"
CHECKSUM_PREFIX = b"#~checksum: "
VECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9.-]*$")


class Failure(Exception):
    """The suite could not be run as recorded."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def covered_bytes(data):
    """Every byte except the root checksum line and its terminator (FORMAT.md R3)."""
    return b"".join(
        line for line in data.splitlines(keepends=True)
        if not line.startswith(CHECKSUM_PREFIX)
    )


def recompute_checksum(data):
    """SHA-512/256 of the covered bytes in standard padded base64 (R1, R3, R4)."""
    return base64.b64encode(hashlib.new("sha512_256", covered_bytes(data)).digest()).decode()


def stated_checksum(data):
    for line in data.splitlines():
        if line.startswith(CHECKSUM_PREFIX):
            return line[len(CHECKSUM_PREFIX):].decode()
    return None


def path_of(vector):
    return (HERE / vector["file"]).resolve()


def checker_pinned_digest():
    """The base-schema digest validate_fhgm.py pins, read as text.

    Imported by parsing rather than by execution: the offline lane runs with the
    standard library alone, and the toolkit is not installed there.
    """
    text = CHECKER.read_text(encoding="utf-8")
    match = re.search(r'^BASE_SHA256 = "([0-9a-f]{64})"$', text, re.MULTILINE)
    if not match:
        raise Failure("cannot read BASE_SHA256 from validate_fhgm.py")
    return match.group(1)


def verify_provenance(provenance, base_schema):
    """Refuse to report a pass when a recorded artifact changed under the manifest."""
    problems = []
    record = provenance["baseSchema"]
    pinned = checker_pinned_digest()
    if record["sha256"] != pinned:
        problems.append(f"provenance base schema {record['sha256']} != the checker's BASE_SHA256 "
                        f"{pinned}")
    if base_schema is not None:
        data = base_schema.read_bytes()
        if sha256(data) != record["sha256"]:
            problems.append(f"supplied base schema {sha256(data)} != provenance {record['sha256']}")
        if len(data) != record["size"]:
            problems.append(f"supplied base schema size {len(data)} != provenance {record['size']}")
    for group in ("contractArtifacts", "vectorGenerators"):
        for artifact in provenance[group]:
            path = REPO / artifact["local"]
            if not path.is_file():
                problems.append(f"{artifact['local']}: recorded artifact is missing")
                continue
            data = path.read_bytes()
            if sha256(data) != artifact["sha256"]:
                problems.append(f"{artifact['local']}: sha256 {sha256(data)} != provenance "
                                f"{artifact['sha256']} (re-record provenance.json after a "
                                "contract or generator change, then re-seal the manifest)")
            elif len(data) != artifact["size"]:
                problems.append(f"{artifact['local']}: size {len(data)} != provenance {artifact['size']}")
    return problems


def check_downstream_pins(provenance):
    """Advisory lane: are the draft pins consumers hold still pointing at our bytes?"""
    from urllib.request import Request, urlopen

    problems = []
    for pin in provenance.get("downstreamPins", []):
        tracked = REPO / pin["tracks"]
        local = sha256(tracked.read_bytes())
        request = Request(pin["url"], headers={"Accept": "application/json",
                                               "User-Agent": "fhgm-conformance-pin-freshness"})
        try:
            with urlopen(request, timeout=60) as response:
                document = json.loads(response.read())
        except Exception as error:  # noqa: BLE001 - network lane, report whatever happened
            problems.append(f"{pin['name']}: could not read {pin['url']}: {error}")
            continue
        node = document
        for part in pin["pointer"].strip("/").split("/"):
            node = node[part]
        remote = node.get(pin["field"])
        state = "fresh" if remote == local else "STALE"
        print(f"{state}: {pin['name']} records {pin['field']} {remote} for {pin['tracks']}; "
              f"this tree holds {local}")
        if remote != local:
            problems.append(
                f"{pin['name']}: pinned digest {remote} != current bytes {local}. Refresh the pin "
                "in the consumer repository against the merged commit, never before it merges.")
    return problems


def predecessors_of(vector):
    context = vector.get("context") or {}
    return [(HERE / path).resolve() for path in context.get("predecessors", [])]


# --- lanes ------------------------------------------------------------------

def generator_deps_available():
    """The generators import PyYAML and jsonschema through the pilot helpers."""
    import importlib.util

    return all(importlib.util.find_spec(name) for name in ("yaml", "jsonschema"))


def regenerate(vectors):
    """Rebuild every generated vector in a temporary tree and compare bytes."""
    wanted = {vector["id"]: vector for vector in vectors if vector["generator"] != "committed"}
    produced = {}
    if not wanted:
        return produced
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for kind in {vector["generator"] for vector in wanted.values()}:
            if kind == "embed_models":
                continue
            script = GENERATORS.get(kind)
            if script is None or not script.is_file():
                raise Failure(f"unknown generator {kind!r}")
            target = root / kind
            target.mkdir(parents=True, exist_ok=True)
            result = subprocess.run([sys.executable, str(script), str(target)],
                                    capture_output=True, text=True)
            if result.returncode:
                raise Failure(f"{kind} failed: {result.stderr.strip()[:400]}")
        if any(vector["generator"] == "embed_models" for vector in wanted.values()):
            derived = root / "embed_models" / S6K_DERIVED.name
            derived.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [sys.executable, str(EMBED), str(S6K_PROFILE), str(derived)],
                capture_output=True, text=True)
            if result.returncode:
                raise Failure(f"embed_models failed: {result.stderr.strip()[:400]}")
        for path in root.rglob("*.fhgff3.gff3"):
            produced.setdefault(path.name, path.read_bytes())
    for vector_id, vector in wanted.items():
        name = path_of(vector).name
        if name not in produced:
            raise Failure(f"{vector_id}: {vector['generator']} produced no {name}")
        produced[vector_id] = produced[name] == path_of(vector).read_bytes()
    return produced


class Lanes:
    """The released base schema and the optional GFF3 tool, built once."""

    def __init__(self, base_schema, offline, gff3_tool):
        self.offline = offline
        self.gff3_tool = gff3_tool
        self.base_validator = None
        if not offline:
            import jsonschema

            self.base_validator = jsonschema.Draft202012Validator(
                json.loads(base_schema.read_bytes()),
                format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)

    def base(self, data):
        if self.offline:
            return "skipped", ""
        import yaml

        header = yaml.safe_load(b"".join(
            line[2:] for line in data.splitlines(keepends=True)
            if line.startswith(b"#~")))
        errors = sorted(self.base_validator.iter_errors(header), key=str)
        if not errors:
            return "accept", ""
        error = errors[0]
        return "reject", f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"

    def gff3(self, data):
        if self.offline or not self.gff3_tool:
            return "skipped", ""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vector.fhgff3.gff3"
            path.write_bytes(data)
            result = subprocess.run([self.gff3_tool, "--no-header", str(path)],
                                    capture_output=True, text=True)
        text = (result.stdout + result.stderr).strip()
        return ("accept" if result.returncode == 0 else "reject"), text


def model_lane(vector, data, base_schema):
    """The committed model-level checker over these exact bytes."""
    with tempfile.TemporaryDirectory() as directory:
        current = Path(directory) / "current.fhgff3.gff3"
        current.write_bytes(data)
        command = [sys.executable, str(CHECKER), "--base-schema", str(base_schema)]
        for predecessor in predecessors_of(vector):
            command += ["--predecessor", str(predecessor)]
        command.append(str(current))
        result = subprocess.run(command, capture_output=True, text=True)
    text = (result.stdout + result.stderr).strip()
    return ("pass" if result.returncode == 0 else "reject"), text


# --- verification -----------------------------------------------------------

def check_vector(vector, lanes, base_schema):
    path = path_of(vector)
    if not path.is_file():
        raise Failure(f"{vector['id']}: missing vector file {vector['file']}")
    data = path.read_bytes()
    problems = []

    recorded = vector["bytes"]
    if sha256(data) != recorded["sha256"]:
        problems.append(f"sha256 {sha256(data)} != recorded {recorded['sha256']}")
    if len(data) != recorded["size"]:
        problems.append(f"size {len(data)} != recorded {recorded['size']}")
    stated = stated_checksum(data)
    recomputed = recompute_checksum(data)
    outcome = vector["layers"]["checksum"]
    if outcome == "verify":
        if stated != vector["checksum"]:
            problems.append(f"checksum line {stated} != recorded {vector['checksum']}")
        if recomputed != stated:
            problems.append(f"recorded as verifying, recomputed {recomputed} != stated {stated}")
    elif outcome == "stale":
        if stated != vector["checksum"]:
            problems.append(f"stale vector states {stated}, recorded {vector['checksum']}")
        if recomputed == stated:
            problems.append("recorded as tampered, but the checksum line covers the bytes again")
    else:
        problems.append(f"unknown recorded checksum outcome {outcome!r}")

    if lanes.offline:
        return problems, None
    base, base_text = lanes.base(data)
    model, model_text = model_lane(vector, data, base_schema)
    gff3, gff3_text = lanes.gff3(data)
    layers = vector["layers"]
    if base != layers["base"]:
        problems.append(f"base layer {base} ({base_text}) != recorded {layers['base']}")
    if model != layers["model"]:
        problems.append(f"model layer {model} != recorded {layers['model']}")
    if vector["expected"] == "valid":
        if model != "pass":
            problems.append(f"expected valid, the checker rejected it: {model_text}")
    else:
        if model != "reject":
            problems.append("expected invalid, the checker accepted it")
        if vector["reason"] not in model_text:
            problems.append(f"recorded reason {vector['reason']!r} not in output: {model_text}")
    if gff3 != "skipped" and gff3 != layers["gff3"]:
        problems.append(f"GFF3 layer {gff3} != recorded {layers['gff3']}: {gff3_text}")
    gap = model == "reject" and base == "accept" and recomputed == stated
    return problems, {"base": base, "model": model, "gff3": gff3, "gap": gap}


def seal(manifest):
    """Re-record the mechanical fields; expectations are never rewritten."""
    for vector in manifest["vectors"]:
        data = path_of(vector).read_bytes()
        vector["bytes"] = {"size": len(data), "sha256": sha256(data)}
        vector["checksum"] = stated_checksum(data)
    return json.dumps(manifest, indent=2) + "\n"


# --- census -----------------------------------------------------------------

def census(results, manifest):
    buckets = {rule: {"valid": 0, "invalid": 0, "skipped": 0}
               for rule in manifest["rules"]}
    for result in results:
        for rule in result["cited"]:
            bucket = buckets.setdefault(rule, {"valid": 0, "invalid": 0, "skipped": 0})
            if result["model"] == "skipped":
                bucket["skipped"] += 1
            elif result["expected"] == "valid":
                bucket["valid"] += 1
            else:
                bucket["invalid"] += 1
    return buckets


def report(results, manifest, offline):
    rules = manifest["rules"]
    table = census(results, manifest)
    width = max(len(rule) for rule in rules)
    print(f"\n{'rule':<{width}}  valid  invalid  skipped  covers")
    for rule, summary in rules.items():
        counts = table.get(rule, {"valid": 0, "invalid": 0, "skipped": 0})
        text = summary["summary"]
        if len(text) > 62:
            text = text[:59].rstrip() + "..."
        if summary.get("shared"):
            text = "[shared rule] " + text
        print(f"{rule:<{width}}  {counts['valid']:>5}  {counts['invalid']:>7}  "
              f"{counts['skipped']:>7}  {text}")
    print(f"\n{'open scope':<{width}}  valid  invalid  skipped  states no outcome")
    for rule, summary in manifest["openScope"].items():
        print(f"{rule:<{width}}  {0:>5}  {0:>7}  {0:>7}  {summary['summary'][:62]}")
    valid = sum(1 for result in results if result["expected"] == "valid")
    invalid = len(results) - valid
    rejected = [result for result in results if result["expected"] == "invalid"]
    gaps = [result["id"] for result in rejected if result.get("gap")]
    print(f"\nVectors: {len(results)} recorded ({valid} valid, {invalid} invalid)")
    if offline:
        print("Model lane offline: base, model and gff3 layers were not run.")
        return
    print(f"Gap-proof rejections (the released base schema and the exact-byte checksum "
          f"accept them, only the model-level checker rejects): {len(gaps)}/{len(rejected)}")
    for result in rejected:
        if not result.get("gap"):
            print(f"  not gap-proof: {result['id']} "
                  f"(base={result['base']}, checksum={result['checksum']}, rule={result['rules'][0]})")
    if results and all(result["gff3"] == "skipped" for result in results):
        print("GFF3 feature lane: skipped for every vector (gff3-validate not supplied; it is "
              "a separate tool and no FHGM rule depends on it).")


def manifest_problems(manifest):
    """Every structural claim the manifest makes, checked against this tree.

    Returns a list of human-readable problems; empty means the manifest is
    internally consistent and every byte it cites is present. Kept separate from
    ``main`` so ``tests/test_fhgm_conformance.py`` can feed it broken manifests
    and assert that each defect is caught.
    """
    problems = []
    vectors = manifest["vectors"]
    ids = [vector["id"] for vector in vectors]
    if len(set(ids)) != len(ids):
        problems.append("duplicate vector id in manifest")
    for vector in vectors:
        if not VECTOR_ID.match(vector["id"]):
            problems.append(f"vector id {vector['id']!r} is not kebab-case")
        if not path_of(vector).is_file():
            problems.append(f"{vector['id']}: missing vector file {vector['file']}")
        elif vector["file"].startswith("vectors/") \
                and path_of(vector).name != f"{vector['id']}.fhgff3.gff3":
            # Vectors this suite generates are named by their id. Vectors citing bytes
            # already published under ../examples/ keep those file names and map them to
            # a stable manifest id instead: renaming committed fixture bytes would break
            # the documentation that already cites them, and one snapshot may appear as
            # several vectors under different supplied histories.
            problems.append(f"{vector['id']}: file {vector['file']!r} is not named for the id")
        for rule in ([vector["rule"]] if "rule" in vector else vector.get("rules", [])):
            if rule not in manifest["rules"]:
                problems.append(f"{vector['id']}: cites unknown rule {rule}")
            elif rule in manifest.get("openScope", {}):
                problems.append(f"{vector['id']}: cites open scope {rule} as a rule")
        if (vector["expected"] == "valid") != ("rules" in vector):
            problems.append(f"{vector['id']}: valid vectors cite rules, invalid vectors one rule")
        if (vector["expected"] == "invalid") != ("reason" in vector):
            problems.append(f"{vector['id']}: only invalid vectors record a reason")
        for rule in vector.get("sharedRules", []):
            if rule not in manifest["rules"] or not manifest["rules"][rule].get("shared"):
                problems.append(f"{vector['id']}: cites {rule} as a shared rule but the manifest "
                                "does not record it as one")
        files = {other["file"] for other in vectors}
        for predecessor in predecessors_of(vector):
            relative = vector_relative_file(manifest, predecessor)
            if not predecessor.is_file():
                problems.append(f"{vector['id']}: missing predecessor {predecessor.name}")
            elif relative not in files:
                problems.append(f"{vector['id']}: predecessor {predecessor.name} is not a vector")
            elif relative == vector["file"]:
                problems.append(f"{vector['id']}: a vector cannot be its own predecessor")
    return problems


def vector_relative_file(manifest, absolute):
    for vector in manifest["vectors"]:
        if path_of(vector) == absolute:
            return vector["file"]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-schema", type=Path,
                        help="bytes of the released fhgff3.json the checker pins")
    parser.add_argument("--offline", action="store_true",
                        help="verify bytes, digests and checksums only (standard library)")
    parser.add_argument("--skip-regeneration", action="store_true",
                        help="do not re-run the generators and compare bytes")
    parser.add_argument("--gff3-validate", default=os.environ.get("GFF3_VALIDATE"),
                        help="optional gff3-validate executable for the feature lane")
    parser.add_argument("--seal", action="store_true",
                        help="re-record vector digests and checksums after a clean run")
    parser.add_argument("--check-downstream-pins", action="store_true",
                        help="fetch the draft pins other repositories hold on our contract bytes "
                             "and report whether they are still fresh (network)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.offline and not args.base_schema:
        parser.error("--base-schema is required unless --offline is used")
    if not args.offline and not args.base_schema.is_file():
        raise Failure(f"no base schema at {args.base_schema}")

    manifest = json.loads(MANIFEST.read_text())
    provenance = json.loads((HERE / "provenance.json").read_text())
    vectors = manifest["vectors"]

    problems = verify_provenance(provenance, args.base_schema if not args.offline else None)
    problems += manifest_problems(manifest)
    if problems:
        for problem in problems:
            print(f"record: {problem}")
        raise Failure("the recorded suite does not match this tree")
    record = provenance["baseSchema"]
    if args.offline:
        print(f"Offline lane: provenance verified against this tree ({record['repository']}@"
              f"{record['ref']} base schema digest checked, base/model/GFF3 layers not run).")
    else:
        artifacts = len(provenance["contractArtifacts"]) + len(provenance["vectorGenerators"])
        print(f"Base schema {record['repository']}@{record['ref']} ({record['path']}), sha256 "
              f"{sha256(args.base_schema.read_bytes())}, retrieved {record['retrieved']}; the "
              f"checker pins the same digest. Provenance verified for the base schema and "
              f"{artifacts} recorded artifacts.")

    generated = sum(1 for vector in vectors if vector["generator"] != "committed")
    if args.skip_regeneration:
        print(f"Regeneration check skipped by request: {generated} generated vectors were "
              "compared against their recorded digests only.")
    elif not generator_deps_available():
        print(f"Regeneration check skipped: the generators import PyYAML and jsonschema, which "
              f"this interpreter does not have. {generated} generated vectors were compared "
              "against their recorded digests only.")
    else:
        reproduced = regenerate(vectors)
        bad = sorted(key for key, value in reproduced.items() if value is False)
        if bad:
            raise Failure(f"vectors are not byte-reproducible: {', '.join(bad)}")
        print(f"Regenerated {generated} generated vectors byte-for-byte "
              f"({len(vectors) - generated} committed by hand).")

    lanes = Lanes(args.base_schema, args.offline,
                  args.gff3_validate or shutil.which("gff3-validate"))
    if not args.offline and not lanes.gff3_tool:
        print("gff3-validate not found: the GFF3 feature lane reports skipped for every vector. "
              "It is a separate tool, and no FHGM rule depends on it.")

    results = []
    failed = []
    if args.seal:
        if args.offline:
            raise Failure("--seal requires a non-offline run to verify layer outcomes")
        seal(manifest)
    for vector in vectors:
        problems, outcome = check_vector(vector, lanes, args.base_schema)
        result = {
            "id": vector["id"],
            "expected": vector["expected"],
            "rules": [vector["rule"]] if "rule" in vector else vector["rules"],
            "cited": ([vector["rule"]] if "rule" in vector else vector["rules"])
            + vector.get("sharedRules", []),
            "checksum": vector["layers"]["checksum"],
            "model": "skipped" if args.offline else outcome["model"],
            "base": "skipped" if args.offline else outcome["base"],
            "gff3": "skipped" if args.offline else outcome["gff3"],
            "gap": None if args.offline else outcome["gap"],
        }
        results.append(result)
        if problems:
            failed.append(vector["id"])
            print(f"FAIL {vector['id']}")
            for problem in problems:
                print(f"     {problem}")
        elif args.verbose:
            print(f"ok   {vector['id']:<40} base={result['base']} "
                  f"checksum={vector['layers']['checksum']} gff3={result['gff3']} "
                  f"model={result['model']}")

    if args.seal:
        if failed:
            raise Failure("refusing to seal while vectors mismatch")
        MANIFEST.write_text(seal(manifest))
        print(f"Sealed {MANIFEST.name}: vector sizes, sha256 digests and checksum lines "
              "re-recorded from the bytes on disk.")

    report(results, manifest, args.offline)
    if args.check_downstream_pins:
        print()
        stale = check_downstream_pins(provenance)
        for problem in stale:
            print(f"run_conformance: {problem}")
        if stale:
            return 1
    if failed:
        print(f"\nFAILED {len(failed)} of {len(results)} vectors: {', '.join(failed)}")
        return 1
    mode = "offline (bytes, digests and checksums only)" if args.offline \
        else "base, checksum, model and GFF3 layers as available"
    print(f"\nOK: {len(results)} vectors matched their recorded outcomes ({mode}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Failure as failure:
        print(f"run_conformance: {failure}", file=sys.stderr)
        raise SystemExit(2)
