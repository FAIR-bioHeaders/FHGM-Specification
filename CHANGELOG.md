# FHGM changelog

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
