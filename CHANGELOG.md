# FHGM changelog

## Unreleased — existing K2 text coverage (2026-11-19)

- Add 19 synthetic conformance vectors (81 total: 18 valid, 63 invalid) for
  existing non-ASCII edge-whitespace, invisible-character and required-modelId
  constraints, including an interior-NBSP positive control. Both released-base
  lanes retain every earlier vector and expectation. The clause derivations are
  in `development/conformance/TEXT-COVERAGE-2026-11-19.md`.
- Add a rule-specific coverage guard. No record/transport contract or checker
  changes, consumer repins, publication or support claims. FHGM #32 remains
  open for the Parent and mechanism decisions; #22/#27/#28 remain open.

## Unreleased — model-level checks every guard is tested by (2026-11-18)

- Mutation testing showed several checker guards that no vector noticed. Eleven
  vectors (58: 16 valid, 42 invalid) and a checker-function test now catch every
  mutation listed in `development/conformance/README.md` ("Mutation check"):
  the K6 assembly-link and record-reference matches, the missing prior model,
  the current-file guard (function test, since no byte vector can reach it), K2
  URI format, and K4 matching only decoded IDs (with a negative control naming
  `toy%2Da` literally).
- K4 now requires the target to be a **root** gene row (no `Parent`); K3 runs
  before the per-record rules (deviation D4) and compares modelIds after NFC
  normalisation.
- Draft record-contract change (`fhgm-model.schema.json`): opaque text is
  trimmed and free of control, zero-width and bidirectional formatting
  characters; `reuseConditions`, `assemblyName` and `deposit` identifiers must
  be non-blank; `evidence[].uri`, `software[].uri` and `methods.protocol` take
  only FORMAT.md R14 schemes. No earlier vector or fixture changes outcome.
- Review follow-through (link host): an http, https or ftp link must name a
  host after optional user information, so `https://user@/`, `https://@/` and
  `ftp://user@/` are rejected although `format: uri` accepts them. The link
  pattern is portable across Python and ECMA-262 regex dialects: an explicit
  whitespace class instead of `\s`, end of string as `(?![\s\S])` rather than
  `$`, no `@` in user information and no bracket in a registered-name host.
  Four vectors (62: 17 valid, 45 invalid) pin it, one rejection per link field
  and one accepted user-info/IPv6 control; matrix re-sealed, 0 verdict changes,
  gap claim 42/45.
- Documented: identity cases v0.1 does not rule on (#28), the attribute-tag
  matching rule (`Name=x; ID=toy-a` does not resolve), and the structural
  defects neither gff3-validator 0.1.0 nor FHGM catches (#27).

## Unreleased — base selection by cited schema URL (2026-11-18)

- `validate_fhgm.py` now selects the FHGFF3 base release by the carrier's
  `schema` URL, mapped through new `schemaUrls` lists in
  `development/model/base-schemas.json`, instead of by `schemaVersion`. It
  refuses a carrier whose URL names no registered release (a superseded release
  such as v0.4.0, or raw `main`), states no URL, or cites a release whose bytes
  were not supplied. The old fallback to the oldest supplied base, which
  judged files by bytes they never cited, is gone.
- Draft transport overlay change: the v0.6.0 identity branch of
  `fhgm-draft.schema.json` gains the FHR-Specification alias URL and admits
  `schemaVersion` `1.1` as well as `1.2`, matching the shared v0.6.0 release.
- The conformance runner hands the checker both base files in both lanes (the
  matrix lane passed only the v0.6.0 bytes before), requires both for any
  non-offline run, and reads the header for its base layer with the toolkit's
  strict reader. Twins keep any citation other than v0.5.0.
- Four vectors (47: 16 valid, 31 invalid): `v0.6.0-citation-stating-1.1`,
  `fhr-specification-alias-v0.6.0`, `carrier-cites-raw-main` and
  `transport-1-0-under-v0.5.0-citation`. `transport-1-0-extension` keeps its
  bytes and layers; its reason moves to the selection refusal. The matrix was
  re-sealed: 0 verdict changes against the sealed lane, gap claim 28/31.

## Unreleased — inherited build hygiene (2026-11-18)

- `requirements.txt` pins `linkml==1.9.6`, `linkml-runtime==1.9.5` and
  `mkdocs==1.6.1`: linkml 1.10 dropped `gen-markdown`, which `make gen` calls.
- The Makefile's JSON Schema target names the real top class (`gff document`)
  instead of the nonexistent `transaction`, which produced a schema with no
  root properties. Committed generated artifacts are not regenerated.
- Removed the unused `jsonschema/gff3-validator-webapp.py` and its template:
  it imported a module that does not exist, hardcoded a Flask `secret_key`
  and ran with `debug=True`. GFF3 validation lives in gff3-validator.

## Unreleased — header copy re-pinned to the shared v0.6.0 release (2026-11-18)

- `header/` now mirrors FAIR-bioHeaders-Specification at the `v0.6.0` release
  tag (commit `0ae18b00`) instead of an untagged 2026-10-21 `main` commit
  (`bdcaecf7`), matching FHGFF3 #19. Every copied file was re-extracted
  byte-for-byte at the tag: 49 copied files (29 unchanged, 10 changed, 10 new
  v0.5.0/v0.6.0 conformance vectors), 4 recorded import digests.
- `header/provenance.json`, `header/PROVENANCE.md`, `header/docs/README.md`
  and `header/conformance/README.md` follow the pin; `header/README.md` now
  names the v0.6.0 schema URL and `schemaVersion` `"1.2"` instead of v0.4.0.
- The shared-conformance CI job moves its toolkit baseline from
  `fair-bioheaders` 0.8.1 to 0.11.0, the release that bundles the v0.6.0
  schemas; 0.8.1 cannot run the v0.6.0 suite.
- The `development/` FHGM draft tree is not touched by this re-pin.

## Unreleased — real-data promotion batch, draft (2026-11-15)

- Per the maintainer promotion decision of 2026-11-15, add the 12 `dmel-*`
  vectors to the conformance census (31 → 43: 14 valid, 29 invalid): the 10
  gap-proof real-data rejections measured by `examples/dmel4/exercise_rules.py`
  plus the two positive anchors their pointer cases require. Emitted by
  `make_dmel_vectors.py` from the committed dmel4 fixtures with one documented
  mutation per case; feature rows remain verbatim RefSeq `GCF_000001215.4`
  chromosome-4 bytes.
- No earlier vector's bytes or expectations change. The manifest file digest
  moves with the added entries; consumer byte-pins refresh in the consumer
  repositories.
- DRAFT promotion: every recorded expectation carries a contract-text
  derivation in `development/conformance/PROMOTION-2026-11-15.md` and requires
  independent review by a reader who is not the derivation's author; the
  promoting PR stays a draft and merges on no agent approval. No FHGM contract,
  schema version, release or toolkit support is introduced (rule V7).

## Unreleased — dual FHGFF3 base support (2026-11-15)

- Per the maintainer decision of 2026-11-15, the draft harness admits both
  released FHGFF3 bases: v0.5.0/schemaVersion 1.1 and v0.6.0/schemaVersion 1.2.
  Selection, not substitution: `development/model/base-schemas.json` registers
  the released bytes by tag-resolved digest, the checker routes each carrier by
  its declared `schemaVersion` and prints the selection, and the transport
  overlay carries two closed identity branches.
- The conformance suite gains the `base_matrix.json` lane: every sealed vector
  is re-observed as a twin under the v0.6.0 bytes. The original 31 vector entries
  keep their bytes and expectations; the 12 promoted vectors are included in
  both lanes. The manifest's rules, open-scope and status text are preserved;
  added entries and dual-base descriptors change its digest, so consumers
  holding byte-pins refresh against the merged commit as their own action.
- Measured in the merged state: 43 twins, 0 verdict changes against the sealed
  lane; the gap claim (27/29 base-and-checksum-passing, model-only rejections)
  holds identically on
  both bases. The dmel4 example lane reproduces the 10 gap-proof real-data
  rejections under the 1.2 identity and now carries the 1.2 transport case as a
  positive control (former finding F1).
- `check_draft.py` and `exercise_rules.py` accept the registered bases and run
the matrix per base with cross-routing checks. Draft status unchanged: no
FHGM contract, schema version, release, w3id/tag URL or toolkit support is
introduced (selection rule V7).

## Unreleased — native draft contract v0.1 proposal (2026-11-12)

- Per the recorded Option C hybrid decision in shared #204, advance the draft
  to a native FHGM model contract (development/model/fhgm-model.schema.json)
  carried by FHGFF3 1.1 x- transport; the overlay becomes transport-only.
- Extend the model-level checker with resolvable/unresolvable/ambiguous
  pointer verdicts and record-versus-file reference agreement.
- Add the committed fixture set under development/examples/model/, update the
  contract fixtures and the revision pilot to the v0.1 record shape with
  recomputed checksums, and derive an S6k record fixture with attributed
  provenance.
- Draft proposal only: no FHGM contract, schema version, release or toolkit
  support is introduced.

## Unreleased — development setup (2026-11-05)

- Establish FHGM identity, contribution guidance and a requirements workspace.
- Add FHGFF3 reuse comparison and worked-example provenance protocol.
- Preserve the inherited pinned header, feature sources and baseline checks.
- No FHGM schema, contract version, release or toolkit support is introduced.

## Inherited FHGFF3 changelog

## Unreleased

- Add always-reporting owned-documentation lint/local-link checks, scheduled and
  manual external-link checks, manual parity diagnostics and a pinned shared
  conformance job using released fair-bioheaders 0.8.1 (#8). Document why parity
  replaces local schema generation/drift under the adopted mirror layout, while
  inherited-model execution remains disabled pending #3. The parent #2 remains
  open; copied header bytes and released contracts are unchanged.

- **Draft/proposal.** Specify the FHGFF3 HTML microdata binding (FHGFF3#5).
  `docs/FHGFF3-MICRODATA.md` defines the FHGFF3 item scope and itemtype (the raw-main
  `fhgff3.json` URL, never the FHR itemtype), fixed-version schema selection, and a
  binding for every FHGFF3 field on top of the shared rules M1 to M4 and R9 in
  `docs/MICRODATA.md`: nested `genomeReference`, `derivedFrom`, `source`,
  `annotationSoftware`, `featureCounts` and `completeness`; ordered author and software
  arrays; single objects versus repeated scalars; zero and `false` versus absence;
  escaped Unicode and text; and the readable-table consistency rule. It carries through
  the schema's alternative genome-reference requirements (an asserted accession/SeqCol
  object **or** a checksum-linked FHR parent), the at-most-one `annotates` relationship
  and the FHR parent-type restriction, and it states that feature counts are producer
  assertions, not GFF3 validation results. It separates structural/schema validity from
  file-backed checksum and parent verification.

  New standalone examples `examples/fhgff3/minimal-reference.microdata.fhgff3.html`,
  `examples/fhgff3/minimal-parent.microdata.fhgff3.html` and
  `examples/fhgff3/rich-microdata.microdata.fhgff3.html` pair with their canonical
  JSON and YAML records, with negative fixtures for the wrong itemtype, an unsupported
  version, malformed nesting, a repeated scalar, script-only content, a missing genome
  link, two `annotates` relationships and a non-FHR `annotates` parent. A **test-only**
  reader, writer and table helper in `tests/fhgff3_microdata.py` (standard library
  `html.parser`), a test-only schema-subset validator in `tests/mini_jsonschema.py` and
  `tests/test_fhgff3_microdata.py` extract the fixtures back to the canonical records,
  compare the readable table with the embedded metadata and reject the negatives.

  This is a proposal for review and publication through FAIR-bioHeaders-Specification.
  The runtime reader and writer remain toolkit work
  ([FAIR-bioHeaders-Tools#58](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/issues/58));
  the website consumer
  ([fair-bioheaders.github.io#27](https://github.com/FAIR-bioHeaders/fair-bioheaders.github.io/pull/27))
  and family builder (fair-bioheaders.github.io#15) are coordinated, not shipped, and
  FHGFF3 HTML microdata output is still unsupported. Website microdata export is enabled
  only after this binding and the round-trip tests pass.

  `.gitignore` no longer hides the hand-written binding document (`docs/*md` still
  ignores the generated docs). The inherited feature-model tree
  (`src/`, `jsonschema/`, `python/`, `rdf/`, `owl/`, `shex/`, `graphql/`, `csv/`) is
  unchanged.
