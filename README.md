# FHGM — FAIR Header Gene Model

FHGM is the development repository for file-bound metadata describing gene-model
contributions, serialized in GFF3. **Native draft contract v0.1 (proposal)
under shared
[#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
review; no publication, no support claims.** Requirements gathering continues;
no FHGM contract, schema version, release or toolkit support is claimed.

Start with [the development plan](development/README.md), the
[FHGFF3 comparison](development/FHGFF3-COMPARISON.md), and the
[worked-example protocol](development/examples/README.md).
The family design record is
[FAIR-bioHeaders-Specification#204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204).
David Molik and Adam Wright jointly hold schema and release authority.

## Design starting point

Reuse FHGFF3's required shared metadata, annotation identity, reference-genome
link, GFF3 header placement and exact-byte checksum rules. Add contribution-level
identity, scope, evidence and revision semantics only where the examples establish
requirements. Decide subtype versus sibling contract through explicit comparison;
repository fork ancestry does not decide schema inheritance.

The payload remains GFF3: native directives and feature relationships are retained.
Distinguish file-level header requirements from feature constraints. Standard GFF3
already represents genes, transcripts, exons and CDS. Any proposed feature-model
extension needs its own demonstrated use case and review.

## Repository layout and inherited baseline

This repository was forked from FAIR-bioHeaders/FHGFF3. Existing files retain their
original identities and provenance; they are not an implemented FHGM schema.

| Path | Role |
| --- | --- |
| `development/` | Active FHGM requirements, comparison and example preparation |
| `header/` | Unmodified pinned FHGFF3 reference baseline, not an editable FHGM model |
| `src/`, `jsonschema/`, `python/`, `rdf/`, `owl/`, `shex/`, `graphql/`, `csv/` | Inherited biodatamodels/gff-schema feature-model material |
| `tests/`, `scripts/`, `.github/workflows/` | Inherited baseline checks and owned documentation checks |
| `docs/` | Inherited/generated documentation and FHGFF3 proposals, not FHGM documentation |

The header pin predates current shared main. Its exact source is recorded in
[header/provenance.json](header/provenance.json); the comparison must select and
record an intentional base before contract work. Never relabel baseline fixtures
as FHGM examples. Finished adopted contracts publish through
[FAIR-bioHeaders-Specification](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification).

## Contributing and checks

Read [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) and the
[CI guide](ci/README.md). Current CI verifies documentation and the inherited
FHGFF3 baseline, **not FHGM validity**. The proposal-stage model-level checker
under [development/model/](development/model/README.md) is review tooling for
shared #204, is not wired into CI, and makes no support claim.
Feature checks belong in
[gff3-validator](https://github.com/FAIR-bioHeaders/gff3-validator); family header
processing belongs in
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools).

## Licensing

New identified FAIR BioHeaders contributions use MPL-2.0 under [LICENSE](LICENSE).
The inherited biodatamodels/gff-schema material has unresolved upstream permissions;
our contribution license does not grant rights in it. Preserve notices and keep
that tree separate from independently authored header work. See
[FHGFF3#3](https://github.com/FAIR-bioHeaders/FHGFF3/issues/3).
