# FHGM changelog

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
