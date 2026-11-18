# FAIR FHGFF3 header development tree

This directory holds the development copy of the **FAIR FHGFF3 header
contract** — the provenance header placed around ordinary GFF3 — as distinct
from the inherited biodatamodels/gff-schema *feature* model elsewhere in this
repository. See the [repository README](../README.md) for the two scopes.

## Contents

| Path | Contents |
| --- | --- |
| [`model/fhgff3_linkml.yml`](model/fhgff3_linkml.yml) | The FHGFF3 LinkML model (imports the shared core `schemas/core.yaml` and `schemas/shared.yaml`) |
| [`docs/FHGFF3.md`](docs/FHGFF3.md) | Development copy of the header documentation (rules G1–G3) |
| [`examples/fhgff3/`](examples/fhgff3) | Examples: checksum and accession-plus-SeqCol genome links, embedded `##FASTA`, no-header, invalid and stale-parent cases |
| [`conformance/`](conformance) | The `fhgff3` valid and invalid conformance vectors |
| [`provenance.json`](provenance.json) | Machine-readable pinned provenance and per-file digests |
| [`PROVENANCE.md`](PROVENANCE.md) | Human-readable provenance and the update procedure |

## Where the contract actually lives

The final, authoritative artifacts publish in the shared repository
**FAIR-bioHeaders-Specification**:

- Model: `fhgff3_linkml.yml`
- Generated contract: `fhgff3.json`, produced by
  `json-schema-generator.py --type fhgff3`; never hand-edited
- Docs: `docs/FHGFF3.md`; format rules: `docs/FORMAT.md`; versions:
  `docs/SCHEMA-VERSIONS.md`
- Examples: `examples/fhgff3/`; vectors: `conformance/`
- Current released schema URL, the release this copy is pinned to:
  <https://w3id.org/fair-bioheaders/fhgff3/v0.6.0> (`schemaVersion` `"1.2"`).
  Earlier releases keep their own URLs (`v0.5.0` for `"1.1"`, `v0.4.0` for
  `"1.0"`); `docs/SCHEMA-VERSIONS.md` in the shared repository lists them all

This tree publishes nothing and has no generator, schema build or release
machinery. Generate, validate and release in the shared repository.

## Active tooling

- **[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools)**
  (`pip install fair-bioheaders`) is the single active family toolkit. Use it to
  add, verify and strip FAIR headers, including FHGFF3.
- **[gff3-validator](https://github.com/FAIR-bioHeaders/gff3-validator)** checks
  the GFF3 features themselves. A header never makes the features valid; run
  feature and biology checks there, separately from the header checks.

The archived FHT-File-Converter is not an active dependency.

## Checking this copy

[`scripts/check_header_parity.py`](../scripts/check_header_parity.py) compares the
copy with the pinned revision and fails on any changed, missing or unlisted file:

```sh
python3 scripts/check_header_parity.py
python3 scripts/check_header_parity.py --upstream ../FAIR-bioHeaders-Specification
```

CI runs the live comparison against the pinned commit
(`.github/workflows/header-parity.yml`). The files are byte-exact; the root
`.gitattributes` disables line-ending conversion for `header/**`.

## Licensing

The copied files under `header/` come from the MPL-2.0 shared publication
repository. The new FAIR BioHeaders files here (this README, `PROVENANCE.md`,
`provenance.json`, `scripts/check_header_parity.py` and the CI workflow) are
MPL-2.0 under the organization's policy and this repository's
[`LICENSE`](../LICENSE). This repository's `LICENSE` inventory does not yet
enumerate the header tree; maintainers should add it when merging.

The inherited gff-schema feature model is **excluded** from that grant and its
upstream permissions remain unresolved
([FHGFF3#3](https://github.com/FAIR-bioHeaders/FHGFF3/issues/3)). Do not reuse it
or fold it into this tree until that is settled. Historical notices are preserved
unchanged.

## Related issues

- Family layout tracker:
  [FAIR-bioHeaders-Specification#107](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/107)
- FHGFF3 header tracker:
  [FHGFF3#2](https://github.com/FAIR-bioHeaders/FHGFF3/issues/2)
- Inherited gff-schema licensing:
  [FHGFF3#3](https://github.com/FAIR-bioHeaders/FHGFF3/issues/3)
