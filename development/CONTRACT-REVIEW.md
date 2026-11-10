# FHGM contract review for David and Adam

Draft decision record for [shared issue #204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204).
The comparison target is [released FHGFF3 1.1](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json).

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

## Compatibility and verification

| Example | Released FHGFF3 1.1 compatibility |
| --- | --- |
| [Minimal](examples/contract/minimal.fhgff3.gff3) and [rich](examples/contract/rich.fhgff3.gff3) | Both pass the base schema with format checking and exact-byte checksum verification. Available GFF3 core checks report zero errors and warnings. |
| [S6k](examples/s6k/README.md) | The headed conversion passes the base contract. The recorded sequence match and separate stop warnings remain visible. |
| [Revision pilot](examples/revision/README.md) | Original, revision and two intentionally bad pointers pass the base contract. The model-level resolution check rejects the wrong-model and stale pointers. An unsupported `derivedFrom.relationship` is rejected by the base. |
| Glys source archive and unconverted deposits | Source material only. They have not been verified as headed FHGFF3 examples. |

The base schema accepts experimental extension content without checking FHGM
semantics. Schema and checksum checks were run separately from the available
GFF3 core checks, which did not run Sequence Ontology or genome-aware checks.
See the [INSDC supplement](INSDC-COVERAGE.md) for the submission boundary.

The [draft validator](model/README.md) implements the proposed overlay for
review. It checks the released file contract, gene targets and immediate
revision pointers with the synthetic fixtures.
