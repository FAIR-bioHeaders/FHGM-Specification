# FHGM contract review for David and Adam

Draft decision record for [shared issue #204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204).
The comparison target is [released FHGFF3 1.1](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json).

Status: native draft contract v0.1 (proposal) under shared #204 review; no
publication, no support claims. The recorded 2026-11-12 decision (Option C
hybrid: native model contract plus FHGFF3-embedded `x-` transport, release
held) is implemented as a draft under the proposed decisions below; the
[2026-11-12 draft contract section](#draft-contract-v01-2026-11-12) records
how, plus reasoned deviations that remain proposals.

## Deposit evidence and field mapping

| Deposit evidence | FHGFF3 reuse | Model requirement or open work |
| --- | --- | --- |
| [S6k](https://doi.org/10.22002/e86gh-a7p16) bundles annotation, transcript and peptide files. The converted pilot verifies two isoforms against the named assembly. | Required `annotation` and `taxon` describe the file and organism. The conditional assembly link is satisfied by the verified `genomeReference`. Optional `scholarlyArticle` and `identifier` distinguish the article and deposit. | Use the gene as the default target and native GFF3 relationships for isoforms. Keep sequence comparisons and CDS stop warnings as separate outcomes. |
| [Glys](https://doi.org/10.22002/apf5b-xyg45) bundles annotation, four transcripts and four peptides, including repeated translations. The inspected archive names a reverse-strand sequence; assembly version is still unverified. | Optional `source` can record the archive and `relatedLink` can identify companion resources. The required genome link cannot be supplied from the scaffold name alone. | Track transcripts by native feature ID rather than by peptide count. Keep this case in source review until the assembly link can be verified. |
| [ABCB7](https://api.datacite.org/dois/10.22002/pr8ks-0fg53) is a version 1.0 Model deposit linked to an article and dataset version family. | Optional `scholarlyArticle`, `identifier` and `reuseConditions` can represent article DOI, deposit DOI and deposit rights. | A repository resource type or version-family link provides no model identity authority. This was a metadata review only. |
| [Corrected synthetase models](https://api.datacite.org/dois/10.22002/hv4eg-wg213) are a version 1.0 Dataset linked to the article and version family. The study compares models across assemblies. | Each FHGFF3 file still needs its own assembly link. Optional `source`, `annotationSoftware` and `annotationProtocol` describe inputs or methods for the file where applicable. | A prior annotation checksum plus model ID and version identifies the predecessor record. Dataset version relations do not establish model supersession. This was a metadata and published-use-case review; the pilot is synthetic. |

Keep `schema`, `schemaVersion`, `version`, `metadataAuthor`, `dateCreated`
and `checksum` at file scope with their FHGFF3 meanings. A model version and
contributor role belong on the model. Article authorship, journal review and
curator acceptance are separate assertions. Record evidence at the narrowest
scope it supports. Use supplied identifiers and roles, and leave unknown
optional values absent. The [source review](examples/PILOT.md) records inspected
archive members, licenses and checksums.

## Proposed decisions

1. **Subtype at the validation layer.** Use the FHGFF3 file contract and a
   separately versioned, explicitly selected FHGM extension validator. Keep the
   released FHGFF3 URI and schema version in the file. After approval, give the
   model contract its own identifier and version separate from those file fields.
   A sibling file type would be warranted if real cases need a different
   subject, incompatible assembly rules or incompatible file semantics.
2. **Ownership.** Develop the model contract and fixtures in FHGM-Specification.
   Coordinate GFF3 checks with gff3-validator and publish a reviewed model
   contract through FAIR-bioHeaders-Specification with David and Adam's approval.
3. **Scope and identity.** Start with one uniquely resolved local feature at
   gene scope. Support explicit transcript scope when curators confirm a
   transcript-only submission use case. Allow a file-local model ID, preserve
   supplied external identifiers with their authorities, and use the snapshot
   checksum with model ID and version for cross-file references. Use the native
   [GFF3 feature graph](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md)
   for isoforms and shared features. Allow noncoding models without CDS or
   protein files.
4. **Revision.** Start with single-predecessor, same-assembly revisions. Treat
   split, merge, and assembly migration as distinct cases requiring examples
   and review. A resolved pointer only identifies the prior record. Record
   acceptance separately with the responsible curator or authority and evidence
   for the decision. The [DataCite relationship vocabulary](https://datacite-metadata-schema.readthedocs.io/en/4.6/appendices/appendix-1/relationType/)
   distinguishes dataset membership and version relations; it does not express
   approval of a model in a particular annotation.
5. **Assembly.** Keep the existing FHGFF3 assembly rule. Use a verified
   accession and SeqCol digest or an FHR link. [GA4GH refget](https://ga4gh.github.io/refget/)
   identifies reference collections from their content. A scaffold name or
   dataset DOI alone cannot establish collection identity.

Ask curators to confirm transcript-only use, identifier minting and authority
for acceptance, using the above defaults as the review proposal. Treat any
change to released FHGFF3 constraints or field meanings as a separate contract
proposal.

## Draft contract v0.1 (2026-11-12)

Native draft contract v0.1 (proposal) under shared #204 review; no
publication, no support claims. Per the recorded Option C hybrid decision, the
[draft model](model/README.md) now states a native FHGM record contract —
[`model/fhgm-model.schema.json`](model/fhgm-model.schema.json), authored as
JSON Schema and enforced per record — carried by FHGFF3 1.1
[`x-` transport](model/README.md#transport-fhgmff3-embedded-records-normative-draft-wording)
under `x-fhgm-models` (FORMAT.md R15). [`model/fhgm-draft.schema.json`](model/fhgm-draft.schema.json)
was reduced to a transport-only overlay; [`model/validate_fhgm.py`](model/validate_fhgm.py)
is the separate model-level checker with the `resolvable` / `unresolvable` /
`ambiguous` verdicts.

Mapping to the proposed decisions above:

| Decision | Draft contract v0.1 |
| --- | --- |
| 1. Subtype at the validation layer | Implemented: the file keeps its released FHGFF3 URI and `schemaVersion` 1.1; FHGM is selected only by explicitly running the checker. The model contract's own in-file identity is not yet expressed — see open questions. |
| 2. Ownership | Implemented: model, checker and fixtures live in this repository's `development/` tree; nothing was published to the shared repository. |
| 3. Scope and identity | Implemented: required `modelId`, `modelVersion` and gene-scope `featureId`; snapshot-checksum identity for cross-file references (`predecessor.annotationChecksum` + model ID + version). |
| 4. Revision | Implemented: single-predecessor, same-assembly pointers, resolved against explicitly supplied snapshots; resolution and curator acceptance stay separate, and the checker never asserts acceptance. |
| 5. Assembly | Implemented at file scope unchanged. At record scope v0.1 requires a `reference` binding mirroring the genome-link alternative — a deviation, below. |

Proposed deviations and extensions, each a draft choice for the maintainers,
not an adoption:

- **Record-level `reference` is required.** #204's premise is that a
  contribution stays interpretable apart from its context; an extracted record
  with no assembly binding loses it. The checker additionally rejects a record
  reference that contradicts, or shares no comparable form with, the file
  genome link (rule 3 in the [model README](model/README.md#model-level-constraints-the-base-schema-cannot-enforce)).
  A reviewer may prefer inheritance from the file header instead; the fixtures
  demonstrate the embedded-binding shape either way.
- **The pointer must name its own `modelId`.** This formalizes the revision
  pilot's assumption that `modelId` is stable across revisions of the same
  model; renames would need split/merge semantics still under review.
- **Version-gap rejection is bounded to supplied snapshots.** A pointer that
  skips a recorded successor present in the supplied predecessor set is
  `unresolvable`. No transitive or external history is claimed — decision 4
  kept transitive history open, and v0.1 only refuses to silently contradict
  the chain the reviewer handed it.
- **Duplicate `modelId` within a snapshot is `ambiguous`, not merely invalid.**
  The identity the pointer needs cannot be selected, so the verdict name is
  part of the interface.

### Open questions for the #204 joint review

v0.1 deliberately does not close:

1. **Final field names.** `modelId`, `modelVersion`, `featureId`, `reference`,
   `predecessor`, `annotates`, `publication.article`/`deposit` and
   `reuseConditions` are proposals; naming consistency with shared objects is
   the shared repository's call.
2. **Is `modelId` curator-assigned or derived?** The S6k-derived fixture uses
   the gene feature ID as a placeholder; who mints stable IDs, and under what
   authority, is unassigned.
3. **`modelVersion` semantics.** v0.1 treats it as opaque (equality/difference
   only). Ordering, comparison or scheme requirements await curator input.
4. **Model-contract identity.** Decision 1 asks for the model contract's own
   identifier and version. v0.1 expresses it only by explicit validator
   selection; whether a contract URI or embedded version marker is added, and
   where it lives given R15, is undecided.
5. **Schema pipeline.** The record contract is hand-authored JSON Schema
   because the PR #10 overlay was; adoption should decide whether it moves to
   the family LinkML chain at shared publication.
6. **Transcript-only scope, split/merge, assembly migration and companion-file
   identity** remain exactly as decision 3/4 left them.

## Compatibility and verification

| Example | Released FHGFF3 1.1 compatibility |
| --- | --- |
| [Minimal](examples/contract/minimal.fhgff3.gff3) and [rich](examples/contract/rich.fhgff3.gff3) | Both pass the base schema with format checking and exact-byte checksum verification. Available GFF3 core checks report zero errors and warnings. |
| [S6k](examples/s6k/README.md) | The headed conversion passes the base contract. The recorded sequence match and separate stop warnings remain visible. |
| [Revision pilot](examples/revision/README.md) | Original, revision and two intentionally bad pointers pass the base contract. The model-level resolution check rejects the wrong-model and stale pointers. An unsupported `derivedFrom.relationship` is rejected by the base. |
| [Contract v0.1 fixtures](examples/model/README.md) | All eleven fixtures — three positives and eight rejections — pass the released base schema and exact-byte checksum; only the model-level checker distinguishes them, per the fixture table. |
| Glys source archive and unconverted deposits | Source material only. They have not been verified as headed FHGFF3 examples. |

The base schema accepts experimental extension content without checking FHGM
semantics. Schema and checksum checks were run separately from the available
GFF3 core checks, which did not run Sequence Ontology or genome-aware checks.
See the [INSDC supplement](INSDC-COVERAGE.md) for the submission boundary.

The [draft model-level checker](model/README.md) implements contract v0.1:
it runs the released base schema, the transport overlay and the native record
contract, then applies the model-level rules and revision-pointer verdicts
against the [contract examples](examples/contract/README.md), the
[committed fixture set](examples/model/README.md) and the
[S6k-derived record fixture](examples/s6k/README.md). `model/check_draft.py`
re-proves each run, including that the released base schema and checksum accept
every model-level rejection fixture. The contract fixtures were updated to the
v0.1 record shape on 2026-11-12 and their checksums recomputed; the v0.1
checker run has not been executed by CI — commands and environment are
recorded in the model README.
