# SPDX-License-Identifier: MPL-2.0
"""Offline integrity checks for the draft FHGM conformance suite.

Runs with the standard library alone, so it works in the documentation and
header-parity lanes where ``fair-bioheaders`` and ``jsonschema`` are not
installed. These tests never run the model checker; they verify what a reviewer
can check without it — that the recorded provenance matches the bytes in the
tree, that every vector's own bytes, digests and file-bound checksum are what the
manifest says, that the manifest is internally consistent and cites only rules it
defines, and that the gap claim the suite makes is arithmetically true.

The model-layer expectations themselves are observed only by
``development/conformance/run_conformance.py``, which reports the base, checksum,
GFF3 and model layers separately.
"""

from base64 import b64encode
from hashlib import new as hash_new
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "development" / "conformance"
MODEL = ROOT / "development" / "model"
RUNNER = CONFORMANCE / "run_conformance.py"
REGISTRY = MODEL / "base-schemas.json"
MATRIX = CONFORMANCE / "base_matrix.json"
VECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
CHECKSUM_PREFIX = b"#~checksum: "
# Rule ids already owned by the shared conformance manifest. A draft FHGM id must
# not collide with one of them, because absorption into the shared suite is an
# open decision of the publication PR.
SHARED_RULE_ID = re.compile(r"^(?:R(?:1[0-5]|[1-9])|M[1-5]|J[1-9]|P[12]|G[1-3]|V[1-7])$")

SPEC = importlib.util.spec_from_file_location("fhgm_run_conformance", RUNNER)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def manifest():
    return json.loads((CONFORMANCE / "manifest.json").read_text())


def provenance():
    return json.loads((CONFORMANCE / "provenance.json").read_text())


def matrix():
    return json.loads(MATRIX.read_text())


def registry():
    return json.loads(REGISTRY.read_text())


def recompute_checksum(data):
    """SHA-512/256 over every byte except the root checksum line, padded base64."""
    covered = b"".join(line for line in data.splitlines(keepends=True)
                       if not line.startswith(CHECKSUM_PREFIX))
    return b64encode(hash_new("sha512_256", covered).digest()).decode()


class ManifestShape(unittest.TestCase):
    def setUp(self):
        self.manifest = manifest()

    def test_top_level_fields(self):
        for field in ("manifestVersion", "status", "specification", "decisionRecord",
                      "checker", "recordContract", "transportOverlay", "provenance",
                      "baseSchema", "baseMatrix", "ruleVocabulary", "contextVocabulary",
                      "layers", "rules", "openScope", "vectors", "retired"):
            with self.subTest(field=field):
                self.assertIn(field, self.manifest)
        self.assertEqual(1, self.manifest["manifestVersion"])

    def test_the_draft_words_the_status_without_becoming_a_release(self):
        status = self.manifest["status"]
        for phrase in ("no released contract", "no schemaVersion", "no schema URL",
                       "versions.json", "V7"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, status)

    def test_vector_ids_are_unique_and_kebab_case(self):
        ids = [vector["id"] for vector in self.manifest["vectors"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate vector id")
        for vector_id in ids:
            with self.subTest(vector=vector_id):
                self.assertRegex(vector_id, VECTOR_ID)

    def test_generated_vectors_are_named_for_their_ids(self):
        for vector in self.manifest["vectors"]:
            if vector["file"].startswith("vectors/"):
                with self.subTest(vector=vector["id"]):
                    self.assertEqual(f"{vector['id']}.fhgff3.gff3", Path(vector["file"]).name)

    def test_cited_rules_exist_and_polarity_is_recorded(self):
        rules = self.manifest["rules"]
        for vector in self.manifest["vectors"]:
            cited = [vector["rule"]] if "rule" in vector else vector["rules"]
            for rule in cited + vector.get("sharedRules", []):
                with self.subTest(vector=vector["id"], rule=rule):
                    self.assertIn(rule, rules)
            with self.subTest(vector=vector["id"]):
                self.assertTrue(vector["description"])
                self.assertIn(vector["expected"], ("valid", "invalid"))
                if vector["expected"] == "valid":
                    self.assertNotIn("rule", vector)
                    self.assertNotIn("reason", vector)
                    self.assertTrue(cited)
                else:
                    self.assertEqual(1, len(cited), "an invalid vector breaks one rule")
                    self.assertTrue(vector["reason"])

    def test_shared_rule_citations_are_marked_shared(self):
        for vector in self.manifest["vectors"]:
            for rule in vector.get("sharedRules", []):
                with self.subTest(vector=vector["id"], rule=rule):
                    self.assertTrue(self.manifest["rules"][rule].get("shared"),
                                    f"{rule} is cited as shared but not recorded that way")

    def test_draft_rule_ids_do_not_collide_with_the_shared_suite(self):
        for rule, summary in self.manifest["rules"].items():
            with self.subTest(rule=rule):
                if summary.get("shared"):
                    self.assertRegex(rule, SHARED_RULE_ID)
                else:
                    self.assertFalse(SHARED_RULE_ID.match(rule),
                                     f"{rule} is already owned by the shared manifest")
                    self.assertRegex(rule, r"^[KB][1-9]$")

    def test_open_scope_ids_are_cited_by_no_vector(self):
        open_ids = set(self.manifest["openScope"])
        for vector in self.manifest["vectors"]:
            cited = set([vector["rule"]] if "rule" in vector else vector["rules"])
            cited |= set(vector.get("sharedRules", []))
            self.assertEqual(set(), cited & open_ids, f"{vector['id']} cites an open-scope id")
        for rule, summary in self.manifest["openScope"].items():
            with self.subTest(scope=rule):
                for field in ("summary", "decision", "vectors"):
                    self.assertTrue(summary[field], f"{rule} has no {field}")

    def test_rule_sources_resolve(self):
        for rule, summary in self.manifest["rules"].items():
            with self.subTest(rule=rule):
                self.assertTrue(summary["summary"])
                source = summary["source"]
                if source.startswith("https://"):
                    continue
                target = (CONFORMANCE / source.split("#", 1)[0]).resolve()
                self.assertTrue(target.is_file(), f"{rule} cites {source}, not in the tree")
                if "#" in source:
                    anchor = source.rsplit("#", 1)[1]
                    text = target.read_text(encoding="utf-8")
                    slugs = {re.sub(r"[^a-z0-9 -]", "", line[3:].strip().lower().replace(" ", "-"))
                             for line in text.splitlines() if line.startswith("## ")}
                    self.assertIn(anchor, slugs,
                                  f"{rule} cites anchor {anchor!r}, which no heading in "
                                  f"{target.name} produces")

    def test_every_model_rule_has_both_polarities(self):
        positive, negative = set(), set()
        for vector in self.manifest["vectors"]:
            cited = [vector["rule"]] if "rule" in vector else vector["rules"]
            for rule in cited:
                (positive if vector["expected"] == "valid" else negative).add(rule)
        for rule, summary in self.manifest["rules"].items():
            if summary.get("shared") or rule.startswith("B"):
                continue
            with self.subTest(rule=rule):
                self.assertIn(rule, positive, "no positive vector")
                self.assertIn(rule, negative, "no negative vector")

    def test_rejected_ids_are_never_reused(self):
        retired = [entry["id"] for entry in self.manifest["retired"]]
        live = [vector["id"] for vector in self.manifest["vectors"]]
        self.assertEqual(set(), set(retired) & set(live))


class Contexts(unittest.TestCase):
    def setUp(self):
        self.manifest = manifest()
        self.by_file = {}
        for vector in self.manifest["vectors"]:
            self.by_file.setdefault(vector["file"], []).append(vector)

    def test_predecessors_exist_and_are_vectors(self):
        for vector in self.manifest["vectors"]:
            for predecessor in (vector.get("context") or {}).get("predecessors", []):
                with self.subTest(vector=vector["id"], predecessor=predecessor):
                    self.assertIn(predecessor, self.by_file,
                                  "a context snapshot must itself be a vector")
                    self.assertTrue((CONFORMANCE / predecessor).is_file())
                    self.assertNotEqual(predecessor, vector["file"],
                                        "a vector cannot be its own predecessor")

    def test_history_is_always_a_recorded_fhgff3_file(self):
        """A supplied snapshot must be structurally valid, whatever its model verdict.

        The checker resolves only the selected file's pointers, so history may
        carry an unresolvable or ambiguous claim of its own - that is the bound
        open scope O6 and O7 describe. What it may not be is a file the released
        schema or the checksum rejects: the suite would then be resolving
        pointers against bytes no reader would accept.
        """
        for vector in self.manifest["vectors"]:
            for predecessor in (vector.get("context") or {}).get("predecessors", []):
                with self.subTest(vector=vector["id"], predecessor=predecessor):
                    cited = self.by_file[predecessor]
                    self.assertTrue(cited, "history is not a recorded vector")
                    self.assertTrue(any(other["layers"]["base"] == "accept"
                                        and other["layers"]["checksum"] == "verify"
                                        for other in cited),
                                    "history is recorded as failing the released layers")

    def test_context_dependence_is_pinned_by_a_pair(self):
        """Deviation D3's bound needs the same bytes to go both ways."""
        by_id = {vector["id"]: vector for vector in self.manifest["vectors"]}
        accepted = by_id["gap-pointer-without-recorded-successor"]
        refused = by_id["gap-skip-with-recorded-successor-supplied"]
        self.assertEqual(accepted["file"], refused["file"])
        self.assertEqual("valid", accepted["expected"])
        self.assertEqual("invalid", refused["expected"])
        self.assertLess(len((accepted.get("context") or {}).get("predecessors", [])),
                        len((refused.get("context") or {}).get("predecessors", [])))


class Bytes(unittest.TestCase):
    def setUp(self):
        self.vectors = manifest()["vectors"]

    def test_recorded_bytes_and_checksums_match_the_files(self):
        for vector in self.vectors:
            path = (CONFORMANCE / vector["file"]).resolve()
            with self.subTest(vector=vector["id"]):
                self.assertTrue(path.is_file(), f"missing {vector['file']}")
                data = path.read_bytes()
                self.assertEqual(vector["bytes"]["size"], len(data), "size drifted")
                self.assertEqual(vector["bytes"]["sha256"], sha256(data).hexdigest(),
                                 "sha256 drifted")
                stated = runner.stated_checksum(data)
                self.assertIsNotNone(stated, "no checksum line")
                self.assertEqual(vector["checksum"], stated, "stated digest drifted")
                verified = recompute_checksum(data) == stated
                self.assertEqual(vector["layers"]["checksum"] == "verify", verified,
                                 "the recorded checksum outcome does not match the bytes")

    def test_covered_bytes_exclude_only_the_checksum_line(self):
        vector = next(v for v in self.vectors if v["id"] == "single-record")
        data = (CONFORMANCE / vector["file"]).read_bytes()
        lines = data.splitlines(keepends=True)
        index = next(i for i, line in enumerate(lines) if line.startswith(CHECKSUM_PREFIX))
        expected = b"".join(line for i, line in enumerate(lines) if i != index)
        self.assertEqual(expected, runner.covered_bytes(data))
        self.assertEqual(len(data) - len(expected), len(lines[index]))
        self.assertEqual(b"\n", lines[index][-1:])

    def test_independent_checksum_matches_the_toolkit_when_present(self):
        try:
            from bioheaders.cli import checksum as toolkit_checksum
        except ImportError:
            self.skipTest("fair-bioheaders is not installed in this interpreter")
        from io import BytesIO

        for vector in self.vectors:
            if vector["layers"]["checksum"] != "verify":
                continue
            data = (CONFORMANCE / vector["file"]).read_bytes()
            with self.subTest(vector=vector["id"]):
                self.assertEqual(recompute_checksum(data),
                                 toolkit_checksum(BytesIO(data), "gff3"))

    def test_vectors_are_pinned_against_line_ending_conversion(self):
        self.assertIn("development/conformance/** -text",
                      (ROOT / ".gitattributes").read_text())


class Provenance(unittest.TestCase):
    def setUp(self):
        self.provenance = provenance()

    def test_base_schema_record_is_complete(self):
        record = self.provenance["baseSchema"]
        for field in ("repository", "url", "ref", "commit", "path", "size", "sha256",
                      "retrieved", "retrievalCommand", "crossCheck", "whyThisRelease"):
            with self.subTest(field=field):
                self.assertTrue(record.get(field), f"{field} is missing")
        self.assertRegex(record["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(record["retrieved"], r"^\d{4}-\d{2}-\d{2}$")

    def test_both_base_records_resolve_tags_and_are_complete(self):
        for key in ("baseSchema", "matrixBaseSchema"):
            record = self.provenance[key]
            for field in ("repository", "url", "ref", "tagObject", "commit", "path", "size",
                          "sha256", "retrieved", "retrievalCommand", "crossCheck",
                          "whyThisRelease"):
                with self.subTest(base=key, field=field):
                    self.assertTrue(record.get(field), f"{field} is missing")
            self.assertRegex(record["ref"], r"^v\d+\.\d+\.\d+$",
                             "released base bytes are recorded by tag, never by a branch")
            self.assertNotEqual(record["ref"], "main")
            self.assertRegex(record["commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(record["retrieved"], r"^\d{4}-\d{2}-\d{2}$")

    def test_base_records_agree_with_the_registry_the_checker_loads(self):
        # No regex over source text: the sidecar is the checker's authority and
        # is compared field-for-field against the suite provenance.
        entries = {e["sha256"]: e for e in registry()["bases"]}
        self.assertEqual(len(entries), len(registry()["bases"]), "duplicate registry digest")
        for key in ("baseSchema", "matrixBaseSchema"):
            record = self.provenance[key]
            with self.subTest(base=key):
                self.assertIn(record["sha256"], entries,
                              f"provenance {key} is not registered for the checker")
                entry = entries[record["sha256"]]
                for field in ("size", "ref", "commit", "path", "schemaVersion",
                              "repository", "tagObject"):
                    self.assertEqual(entry[field], record[field], f"{key}.{field} drifted")
                # acceptsSchemaVersions is registry-only: the suite provenance quotes
                # releases, the enum membership belongs to the checker's sidecar.
                self.assertEqual(entry["schemaVersion"], record["schemaVersion"])

    def test_registry_states_are_coherent(self):
        versions = [e["schemaVersion"] for e in registry()["bases"]]
        self.assertEqual(sorted(versions, key=lambda v: tuple(map(int, v.split(".")))),
                         versions, "registry bases must be listed oldest first")
        for entry in registry()["bases"]:
            with self.subTest(base=entry["ref"]):
                self.assertIn(entry["schemaVersion"], entry["acceptsSchemaVersions"],
                              "a base must state its own schemaVersion")

    def test_registry_schema_urls_select_one_release_each(self):
        """The checker selects a base by the carrier's cited schema URL."""
        seen = {}
        for entry in registry()["bases"]:
            with self.subTest(base=entry["ref"]):
                self.assertTrue(entry["schemaUrls"], "a base must list the URLs that cite it")
                for url in entry["schemaUrls"]:
                    self.assertNotIn(url, seen, f"{url} would select two releases")
                    seen[url] = entry["ref"]
                    self.assertIn(f"/{entry['ref']}", url, "a URL must name its own release")
                    self.assertNotIn("/main/", url, "raw main is not a release")
                for repository in ("FAIR-bioHeaders-Specification", "FHR-Specification"):
                    self.assertIn(f"https://raw.githubusercontent.com/FAIR-bioHeaders/"
                                  f"{repository}/{entry['ref']}/fhgff3.json",
                                  entry["schemaUrls"],
                                  "both repository names are recognised for a release")

    def test_transport_overlay_admits_exactly_the_registered_citations(self):
        overlay = json.loads((MODEL / "fhgm-draft.schema.json").read_text())
        branches = {}
        for branch in overlay["anyOf"]:
            urls = branch["properties"]["schema"]["enum"]
            version = branch["properties"]["schemaVersion"]
            versions = version.get("enum", [version.get("const")])
            refs = {re.search(r"/(v\d+\.\d+\.\d+)", url).group(1) for url in urls}
            self.assertEqual(1, len(refs), "one overlay branch per release")
            branches[refs.pop()] = (sorted(urls), versions)
        for entry in registry()["bases"]:
            with self.subTest(base=entry["ref"]):
                urls, versions = branches[entry["ref"]]
                self.assertEqual(sorted(entry["schemaUrls"]), urls)
                self.assertIn(entry["schemaVersion"], versions)
                for version in versions:
                    self.assertIn(version, entry["acceptsSchemaVersions"],
                                  "the overlay admits a version its release rejects")
                    self.assertNotEqual("1.0", version, "1.0 carries no extension fields")

    def test_base_schema_digests_are_distinct(self):
        digests = [self.provenance[k]["sha256"] for k in
                   ("baseSchema", "matrixBaseSchema")]
        self.assertEqual(2, len(set(digests)), "the two lanes must not share one base")

    def test_manifest_points_at_the_provenance_and_the_matrix(self):
        self.assertIn("provenance.json", manifest()["baseSchema"])
        self.assertEqual("base_matrix.json", manifest()["baseMatrix"])

    def test_recorded_contract_and_generator_bytes_match_the_tree(self):
        artifacts = self.provenance["contractArtifacts"] + self.provenance["vectorGenerators"]
        self.assertTrue(artifacts)
        for artifact in artifacts:
            path = ROOT / artifact["local"]
            with self.subTest(artifact=artifact["local"]):
                self.assertTrue(path.is_file(), "recorded artifact is missing")
                data = path.read_bytes()
                self.assertEqual(artifact["sha256"], sha256(data).hexdigest(),
                                 "digest drifted: re-record provenance.json, then re-seal")
                self.assertEqual(artifact["size"], len(data), "size drifted")

    def test_the_recorded_contract_is_the_one_the_checker_loads(self):
        names = {Path(artifact["local"]).name for artifact in self.provenance["contractArtifacts"]}
        checker = (MODEL / "validate_fhgm.py").read_text()
        for name in ("fhgm-model.schema.json", "fhgm-draft.schema.json"):
            with self.subTest(schema=name):
                self.assertIn(name, names, "the checker's contract is not pinned")
                self.assertIn(name, checker, "the checker no longer loads this file")

    def test_observed_tool_versions_are_recorded(self):
        observed = self.provenance["observedWith"]
        for field in ("python", "fair-bioheaders", "jsonschema", "PyYAML", "gff3-validator",
                      "note"):
            with self.subTest(field=field):
                self.assertTrue(observed.get(field), f"{field} is missing")

    def test_synthetic_content_and_attribution_are_declared(self):
        self.assertIn("synthetic", self.provenance["syntheticContent"]["statement"].lower())
        self.assertIn("CaltechDATA", self.provenance["syntheticContent"]["attribution"])

    def test_downstream_draft_pins_are_tracked_for_the_freshness_lane(self):
        pins = self.provenance["downstreamPins"]
        self.assertTrue(pins, "a draft pin another repository holds on our bytes must be tracked")
        for pin in pins:
            with self.subTest(pin=pin["name"]):
                self.assertTrue((ROOT / pin["tracks"]).is_file())
                self.assertIn(pin["field"], ("sha256", "commit", "suiteManifestSha256"))
                self.assertTrue(pin["asOf"])
                self.assertTrue(pin["checkedBy"])


class Census(unittest.TestCase):
    def setUp(self):
        self.vectors = manifest()["vectors"]

    def test_a_model_rejection_is_gap_proof_unless_the_base_layer_already_catches_it(self):
        rejected = [vector for vector in self.vectors if vector["layers"]["model"] == "reject"]
        self.assertTrue(rejected)
        for vector in rejected:
            boundary = vector["rule"].startswith("B")
            with self.subTest(vector=vector["id"]):
                caught_by_released_layers = (vector["layers"]["base"] == "reject"
                                             or vector["layers"]["checksum"] == "stale")
                self.assertEqual(boundary, caught_by_released_layers,
                                 "the gap claim and the recorded layers disagree")
        gaps = [vector for vector in rejected if not vector["rule"].startswith("B")]
        self.assertEqual(len(rejected) - len([v for v in rejected if v["rule"].startswith("B")]),
                         len(gaps))

    def test_positive_vectors_pass_every_recorded_layer(self):
        for vector in [v for v in self.vectors if v["expected"] == "valid"]:
            with self.subTest(vector=vector["id"]):
                self.assertEqual("accept", vector["layers"]["base"])
                self.assertEqual("verify", vector["layers"]["checksum"])
                self.assertEqual("accept", vector["layers"]["gff3"])
                self.assertEqual("pass", vector["layers"]["model"])

    def test_readme_lists_every_vector(self):
        text = (CONFORMANCE / "README.md").read_text()
        documented = set(re.findall(r"^\| `([a-z0-9.-]+)` \|", text, re.MULTILINE))
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                self.assertIn(vector["id"], documented,
                              "the README census table must list every manifest vector")

    def test_nothing_in_the_suite_claims_a_released_fhgm_identity(self):
        """Rule V7: the draft takes no release form, not even in a fixture byte."""
        for path in sorted(CONFORMANCE.rglob("*")):
            if not path.is_file() or path.suffix not in (".json", ".gff3", ".md", ".py"):
                continue
            with self.subTest(path=path.name):
                self.assertNotIn("w3id.org/fair-bioheaders/fhgm",
                                 path.read_text(encoding="utf-8", errors="ignore"))


class Runner(unittest.TestCase):
    def test_offline_lane_passes_and_reports_skipped_lanes(self):
        result = subprocess.run([sys.executable, str(RUNNER), "--offline"],
                                capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("vector checks matched their recorded outcomes", result.stdout)
        self.assertIn("skipped", result.stdout)
        self.assertIn("Matrix integrity", result.stdout)

    def test_sealing_is_idempotent_on_the_committed_manifest(self):
        """Recorded digests are current, and sealing cannot rewrite an expectation."""
        sealed = runner.seal(manifest())
        self.assertEqual((CONFORMANCE / "manifest.json").read_text(), sealed)

    def test_validation_rejects_a_broken_manifest(self):
        first = lambda document: document["vectors"][0]
        invalid = lambda document: next(v for v in document["vectors"]
                                        if v["expected"] == "invalid")
        with_context = lambda document: next(v for v in document["vectors"]
                                             if (v.get("context") or {}).get("predecessors"))
        defects = {
            "duplicate id": lambda document: document["vectors"].append(dict(first(document))),
            "unknown rule": lambda document: first(document).update(rules=["K9"]),
            "unknown shared rule": lambda document: first(document).update(sharedRules=["R77"]),
            "missing reason": lambda document: invalid(document).pop("reason"),
            "valid must not record a reason": lambda document: invalid(document).update(
                expected="valid"),
            "invalid must not cite a rule list": lambda document: invalid(document).update(
                rules=["K2"]),
            "missing file": lambda document: first(document).update(
                file="vectors/valid/not-here.fhgff3.gff3"),
            "file not named for the id": lambda document: first(document).update(
                file="vectors/valid/supplied-external-model-id.fhgff3.gff3"),
            "self predecessor": lambda document: with_context(document)["context"][
                "predecessors"].append(with_context(document)["file"]),
            "unknown predecessor": lambda document: with_context(document)["context"][
                "predecessors"].append("../examples/contract/rich.fhgff3.gff3"),
            "open scope citation": lambda document: first(document).update(rules=["O1"]),
        }
        for name, defect in defects.items():
            with self.subTest(defect=name):
                document = manifest()
                try:
                    defect(document)
                except (KeyError, IndexError, TypeError, StopIteration) as error:
                    self.fail(f"defect {name!r} does not apply to the manifest: {error}")
                problems = runner.manifest_problems(document)
                self.assertTrue(problems, "the runner accepted a broken manifest")


class Twins(unittest.TestCase):
    """The base_matrix lane: derivation, sealing and defect detection."""

    def setUp(self):
        self.manifest = manifest()
        self.matrix = matrix()
        self.by_id = {vector["id"]: vector for vector in self.manifest["vectors"]}
        self.entries = {entry["id"]: entry for entry in self.matrix["vectors"]}

    def test_matrix_covers_every_vector_exactly_once(self):
        self.assertEqual(sorted(self.by_id), sorted(self.entries))

    def test_sealed_twins_re_derive_from_the_committed_bytes(self):
        self.assertEqual([], runner.verify_twins(self.matrix, self.manifest))

    def test_twin_changes_only_the_identity_and_checksum_lines(self):
        for vector in self.manifest["vectors"]:
            data = runner.path_of(vector).read_bytes()
            derived, method, _ = runner.twin_bytes(data, vector["layers"]["checksum"])
            with self.subTest(vector=vector["id"]):
                if method == "as-committed-1-0":
                    self.assertEqual(data, derived)
                    continue
                changed = [
                    (old, new) for old, new in zip(data.splitlines(), derived.splitlines())
                    if old != new
                ]
                self.assertEqual(len(data.splitlines()), len(derived.splitlines()))
                # Only a v0.5.0 citation moves; any other citation is kept.
                cites_v050 = any(line.startswith(b"#~schema: ") and b"/v0.5.0" in line
                                 for line in data.splitlines())
                expected_lines = (2 if cites_v050 else 1) + (
                    1 if vector["layers"]["checksum"] == "verify" else 0)
                self.assertEqual(expected_lines, len(changed),
                                 "expected a v0.5.0 schema line, schemaVersion and (unless "
                                 "stale) checksum lines to move")
                for old, new in changed:
                    self.assertTrue(old.startswith(b"#~schema: ")
                                    or old.startswith(b"#~schemaVersion: ")
                                    or old.startswith(b"#~checksum: "),
                                    f"unexpected line moved: {old[:40]!r}")
                # records and feature bytes are untouched by construction:
                strip = lambda b: b"".join(  # noqa: E731
                    line for line in b.splitlines(keepends=True)
                    if not line.startswith((b"#~schema: ", b"#~schemaVersion: ",
                                            b"#~checksum: ")))
                self.assertEqual(strip(data), strip(derived))

    def test_twin_derivation_is_deterministic(self):
        for vector in self.manifest["vectors"]:
            data = runner.path_of(vector).read_bytes()
            with self.subTest(vector=vector["id"]):
                self.assertEqual(runner.twin_bytes(data, vector["layers"]["checksum"]),
                                 runner.twin_bytes(data, vector["layers"]["checksum"]))

    def test_stale_twin_keeps_the_stated_digest_stale(self):
        vector = self.by_id["tampered-record-bytes"]
        data = runner.path_of(vector).read_bytes()
        derived, _, _ = runner.twin_bytes(data, "stale")
        self.assertEqual(runner.stated_checksum(derived), runner.stated_checksum(data))
        self.assertNotEqual(runner.recompute_checksum(derived),
                            runner.stated_checksum(derived))

    def test_verified_twin_carries_a_fresh_correct_digest(self):
        for vector in self.manifest["vectors"]:
            if runner.stated_schema_version(runner.path_of(vector).read_bytes()) == "1.0":
                continue  # as-committed: a 1.0 identity is its own defect, no rewrite
            if vector["layers"]["checksum"] != "verify":
                continue
            data = runner.path_of(vector).read_bytes()
            derived, method, _ = runner.twin_bytes(data, "verify")
            with self.subTest(vector=vector["id"]):
                self.assertEqual("identity-rewrite", method)
                self.assertEqual(runner.recompute_checksum(derived),
                                 runner.stated_checksum(derived))

    def test_rewrite_of_a_non_1_1_carrier_refuses(self):
        # The vacuous-control guard: feeding an already-1.2 file must raise,
        # not silently "rewrite" it.
        sealed = self.by_id["both-reference-forms"]
        data = runner.path_of(sealed).read_bytes()
        derived, _, _ = runner.twin_bytes(data, "verify")
        with self.assertRaises(runner.Failure):
            runner.twin_bytes(derived, "verify")

    def test_matrix_problems_catches_broken_records(self):
        defects = {
            "missing twin": lambda d: d["vectors"].pop(0),
            "extra twin": lambda d: d["vectors"].append(dict(d["vectors"][0])),
            "duplicate id": lambda d: d["vectors"].append(dict(d["vectors"][1])),
            "flipped agreement": lambda d: next(
                e for e in d["vectors"] if e["sameAsSealed"]).update(sameAsSealed=False),
            "changed polarity": lambda d: d["vectors"][0].update(expected="invalid"),
            "unknown method": lambda d: d["vectors"][0].update(method="sideways"),
            "layers edited under agreement": lambda d: next(
                e.update(layers=dict(e["layers"], model="reject"))
                for e in d["vectors"] if e["sameAsSealed"] and e["layers"]["model"] == "pass"),
        }
        for name, defect in defects.items():
            with self.subTest(defect=name):
                document = json.loads(MATRIX.read_text())
                try:
                    defect(document)
                except (KeyError, IndexError, TypeError, StopIteration) as error:
                    self.fail(f"defect {name!r} does not apply: {error}")
                problems = runner.matrix_problems(document, self.manifest)
                self.assertTrue(problems, "the runner accepted a broken matrix")


def load_checker():
    """Import validate_fhgm.py, or None where the toolkit is not installed.

    FHGM_CHECKER may name another copy of the checker (a mutation-testing
    harness points it at a neutered copy to confirm these tests notice).
    """
    if not (importlib.util.find_spec("bioheaders") and importlib.util.find_spec("jsonschema")):
        return None
    import os

    path = Path(os.environ.get("FHGM_CHECKER", MODEL / "validate_fhgm.py"))
    spec = importlib.util.spec_from_file_location("fhgm_validate_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipIf(load_checker() is None, "fair-bioheaders and jsonschema are not installed")
class CheckerGuards(unittest.TestCase):
    """Guards no byte vector can reach, exercised on the checker's functions."""

    def setUp(self):
        self.checker = load_checker()

    def test_a_pointer_naming_the_current_file_is_unresolvable(self):
        # A pointer can never honestly name the checksum of the file carrying
        # it (the pointer text is inside the bytes that checksum covers), so no
        # vector can exercise this guard. Feed resolve_predecessor a header whose
        # checksum equals the pointer, with that snapshot also supplied as
        # history and every other condition for "resolvable" met.
        reference = {"genomeReference": {"accession": "SYNTHETIC_ASSEMBLY.1",
                                         "seqcol_id": "A" * 32}}
        current = "C" * 43 + "="
        prior = {"modelId": "model-a", "modelVersion": "1", "featureId": "toy-a",
                 "reference": reference}
        model = dict(prior, modelVersion="2", predecessor={
            "annotationChecksum": current, "modelId": "model-a", "modelVersion": "1"})
        header = {"checksum": current, "genomeReference": reference["genomeReference"]}
        verdict, detail = self.checker.resolve_predecessor(
            "model-a", model, header, {current: (header, {"model-a": prior})})
        self.assertEqual(self.checker.UNRESOLVABLE, verdict)
        self.assertIn("is the current file", detail)
        # Control: the same pointer into a different supplied snapshot resolves.
        other = "D" * 43 + "="
        moved = dict(model, predecessor=dict(model["predecessor"], annotationChecksum=other))
        verdict, _ = self.checker.resolve_predecessor(
            "model-a", moved, header,
            {other: (dict(header, checksum=other), {"model-a": prior})})
        self.assertEqual(self.checker.RESOLVABLE, verdict)

    def test_attribute_keys_match_exactly(self):
        # GFF3 attribute tags are case-sensitive and whitespace is not trimmed:
        # "Name=x; ID=toy-a" carries the tag " ID", not "ID", so that row has no
        # ID, and only the percent-decoded value is indexed.
        rows = (b"toy\tpilot\tgene\t1\t9\t.\t+\t.\tName=x; ID=toy-a\n"
                b"toy\tpilot\tgene\t1\t9\t.\t+\t.\tid=toy-b\n"
                b"toy\tpilot\tgene\t1\t9\t.\t+\t.\tID=toy%2Dc\n")
        targets = self.checker.gene_targets(rows)
        self.assertEqual({b"toy-c"}, set(targets))


if __name__ == "__main__":
    unittest.main()
