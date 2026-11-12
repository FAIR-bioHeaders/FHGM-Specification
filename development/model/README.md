# Draft FHGM native model contract v0.1 (proposal)

Status: native draft contract v0.1 (proposal) under shared
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
review; no publication, no support claims. This is the Option C hybrid adopted
2026-11-12: a native FHGM model contract carried by FHGFF3-embedded `x-`
transport. Nothing here is an adopted contract: no `schemaVersion`, no w3id
schema URL and no `schemas/versions.json` entry exists or is claimed for FHGM.
Publication stays with the shared specification after joint maintainer review.

The draft advances the PR #10 overlay. The record contract is authored directly
as JSON Schema in `fhgm-model.schema.json`; the family LinkML generation chain
is one of the integration questions for shared review (see
[the contract review](../CONTRACT-REVIEW.md)).

## Record fields

One FHGM record describes one contributed gene model inside an annotation
file. File-scope fields (`schema`, `schemaVersion`, `annotation`, `taxon`,
`version`, `metadataAuthor`, `dateCreated`, `checksum` and the FHGFF3 genome
link) keep their released FHGFF3 1.1 meanings at file scope. Concept citations
name the [#204 requirement rows](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204);
they are draft rationales, not adopted semantics.

| Field | Requiredness | #204 concept | Draft rationale |
| --- | --- | --- | --- |
| `modelId` | Required, one opaque string | Model identity and scope | Unique within one annotation snapshot; stable across a revision of the same model on the same assembly. Who mints it — curator or derivation — is open. |
| `modelVersion` | Required, one opaque string | Model identity and scope | Version semantics are open; v0.1 only requires an immediate revision to use a different value from its predecessor. No ordering is implied or checked. |
| `featureId` | Required, one opaque string | Model identity and scope | Exact decoded local GFF3 feature ID. v0.1 resolves one `gene` row; isoforms stay in the native `ID`/`Parent` graph; transcript-only scope awaits curator review. Resolution is a checker rule, not a schema constraint. |
| `reference` | Required; `genomeReference` (accession + supplied SeqCol digest) and/or `annotates` (FHR parent checksum) | Reference coordinates | Mirrors the FHGFF3 genome-link alternative so the record survives extraction from its file. The checker rejects a record reference that contradicts the file genome link. Never inferred; values are producer-supplied assertions. |
| `predecessor` | Optional; then `annotationChecksum` + `modelId` + `modelVersion` all required | New and revised models | The revision pointer proven necessary in the pilots: prior annotation snapshot checksum, model ID and version. Absent means no revision claim. v0.1 supports single-predecessor, same-assembly revision only; split, merge and assembly migration stay open. |
| `contributors` | Optional nonempty list of `{name, role, nameType?, uri?}` | Credit and publication | Supplied model contributors and roles; author objects mirror the shared FHGFF3 `Author`. File metadata authors stay in `metadataAuthor`; article authorship, journal review and curator acceptance stay outside the record. |
| `evidence` | Optional nonempty list of `{description, uri?}` | Evidence and methods | Supplied evidence assertions. An assertion is not a validation result; feature and biology checks belong to gff3-validator and reference matching to its own inputs. |
| `methods` | Optional object: `software[] {name, version?, uri?}`, `protocol` URI, `limitations[]` | Evidence and methods | Tools with versions, a curation protocol reference and supplied limitations or uncertainty. Software objects mirror the FHGFF3 `Software` role. |
| `publication` | Optional object: `article` DOI, `deposit` curie list | Credit and publication | Article and deposited model data keep separate, independently resolvable identities; assembly identity stays in `reference`. Patterns mirror the FHGFF3 `scholarlyArticle` and `identifier` fields. |
| `reuseConditions` | Optional string | Packaging and integrity | Reuse terms supplied for the record; never inferred from the article or file license. |

Nested objects are closed (`additionalProperties: false`), matching the base
header's rule that unknown keys are invalid everywhere except top-level `x-`
keys. Unknown optional values stay absent.

## Model-level constraints the base schema cannot enforce

The pilots (FHGM-Specification PRs #3/#4, summarized in the shared
`docs/FHGM.md`) showed the released FHGFF3 1.1 schema accepts a revision
pointer that names an unchanged neighbor model or a stale predecessor file:
those files pass schema and integrity checks unchanged. These rules therefore
live in the separate model-level checker below, not in any JSON Schema:

1. `modelId` is unique within one snapshot; a collision makes the identity
   ambiguous and the snapshot invalid.
2. `featureId` resolves to exactly one local `gene` row (percent-decoded).
3. A record `reference` shares at least one comparable form with the file
   genome link and never contradicts it.
4. A predecessor pointer resolves against explicitly supplied prior snapshots
   only; the successor's assembly link and record reference must match the
   predecessor's, the versions must differ, and — when the supplied set
   contains a recorded successor of the pointed record — the pointer must name
   that successor rather than skip it (version-gap misuse).

## Transport: FHGFF3-embedded records (normative draft wording)

This section is draft normative text for the adopted Option C transport; it
grants nothing and changes no released contract.

- An FHGM-carrying file **must** be a valid FHGFF3 1.1 file and **must** keep
  the released FHGFF3 `schema` URI and `schemaVersion` `"1.1"`. FHGM adds no
  file-type identity at v0.1; selection happens by explicitly running the
  model-level checker, per the recorded decision.
- Model records **must** be carried under the single top-level extension key
  `x-fhgm-models` as a sequence of one or more objects, per
  [FORMAT.md R15](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
  (extension fields exist from FHGFF3 `schemaVersion` `"1.1"`). Repeatable
  records ride the array; each record **must** satisfy the native contract
  above.
- The extension **never** overrides a standard field (R15). The file checksum
  **covers** the record bytes like every other header byte (R3): editing any
  record changes the file checksum, and the checksum covers the records — not
  any external model registry.
- The base schema validates the **transport only**: header structure, the
  genome link and the presence of the array. Model meaning — targets,
  identity, pointers — is validated exclusively by the separate draft checker
  (`validate_fhgm.py`). A file that passes base schema, checksum and transport
  has **not** passed FHGM validation.
- Pointer resolution is reported by the checker as one of three verdicts and
  resolution **never** asserts curator acceptance of a revision; acceptance is
  a separate decision with its own evidence, recorded outside the header
  check.

### Checker verdicts

For each record with a `predecessor`, given the explicitly supplied prior
snapshots (each of which must itself pass all checks):

- `resolvable` — exactly one prior record matches the pointer identity, on a
  matching assembly, with a changed version and no skipped recorded successor.
- `unresolvable` — zero matches: the snapshot is absent or is the current
  file, the pointer names another model ID, the prior record or its recorded
  version differs, the version is reused, the assembly links conflict or share
  no comparable form, or a recorded successor of the pointed record was skipped.
- `ambiguous` — the pointer identity cannot select one record because multiple
  records share a `modelId` within a snapshot. Ambiguity is a defect of the
  snapshot itself and rejects it.

v0.1 accepts only `resolvable`; `unresolvable` and `ambiguous` exit non-zero
with the reason. Even a `resolvable` verdict states only that the pointer
identifies its predecessor record.

## Running the draft checker

Use Python with `fair-bioheaders` (the checker reuses its GFF3 header reader
and checksum implementation) and `jsonschema`. From the FHGM repository root,
with the released v0.5.0 base schema (the checker pins its bytes):

```sh
git -C /path/to/FAIR-bioHeaders-Specification show v0.5.0:fhgff3.json > /tmp/fhgff3-v0.5.0.json
python development/model/validate_fhgm.py --base-schema /tmp/fhgff3-v0.5.0.json \
  --predecessor development/examples/contract/minimal.fhgff3.gff3 \
  development/examples/contract/rich.fhgff3.gff3
python development/model/check_draft.py /tmp/fhgff3-v0.5.0.json
```

`check_draft.py` is the draft self-test: it regenerates
[`../examples/model/`](../examples/model/README.md) byte-for-byte, runs every
acceptance and rejection fixture against the checker, and re-proves that the
base schema alone accepts the model-invalid files. Run `gff3-validate
--no-header` separately for GFF3 syntax and feature-graph checks; reference
sequence matching and biological evidence assessment require their own inputs.
See the [INSDC supplement](../INSDC-COVERAGE.md) for the coverage boundary:
the experimental records add no coverage to any released contract.
