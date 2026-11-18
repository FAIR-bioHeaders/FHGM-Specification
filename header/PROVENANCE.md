# Pinned provenance

`header/` is a development copy of the **FAIR FHGFF3 header contract**, taken
byte-for-byte from the shared publication repository. It is not derived from the
inherited biodatamodels/gff-schema feature model in this repository.

- **Repository:** `FAIR-bioHeaders/FAIR-bioHeaders-Specification`
- **URL:** <https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification>
- **Ref:** `v0.6.0`
- **Commit:** `0ae18b00ee4bd71ab2dc28bae706b0f9d195076b`
- **Commit date:** 2026-11-13 17:51:21 -0600
- **Commit subject:** `Release v0.6.0 (dotted BUSCO dataset versions: FHP and FHGFF3 1.2, FHR 2.1 unchanged) (#229)`

The machine-readable record is [`provenance.json`](provenance.json). It gives the
pinned commit and the size and SHA-256 digest of every copied file and of every
shared file the copy imports but does not vendor. The commit above is the
`v0.6.0` release tag of the shared repository, the current shared release; it is
recorded, not invented.

## Files copied

Each row is `upstream path` → `local path`, byte-for-byte.

| Upstream (pinned commit) | Local (`header/`) |
| --- | --- |
| `fhgff3_linkml.yml` | `header/model/fhgff3_linkml.yml` |
| `docs/FHGFF3.md` | `header/docs/FHGFF3.md` |
| `examples/fhgff3/annotation.fhgff3.gff3` | `header/examples/fhgff3/annotation.fhgff3.gff3` |
| `examples/fhgff3/annotation.fhgff3.yaml` | `header/examples/fhgff3/annotation.fhgff3.yaml` |
| `examples/fhgff3/embedded-fasta.fhgff3.gff3` | `header/examples/fhgff3/embedded-fasta.fhgff3.gff3` |
| `examples/fhgff3/genome.fhr.fasta` | `header/examples/fhgff3/genome.fhr.fasta` |
| `examples/fhgff3/header-invalid.fhgff3.gff3` | `header/examples/fhgff3/header-invalid.fhgff3.gff3` |
| `examples/fhgff3/minimal-reference.fhgff3.json` | `header/examples/fhgff3/minimal-reference.fhgff3.json` |
| `examples/fhgff3/no-header.gff3` | `header/examples/fhgff3/no-header.gff3` |
| `examples/fhgff3/rich.fhgff3.yaml` | `header/examples/fhgff3/rich.fhgff3.yaml` |
| `examples/fhgff3/stale-parent.fhgff3.gff3` | `header/examples/fhgff3/stale-parent.fhgff3.gff3` |
| `conformance/valid/fhgff3-bgzf.fhgff3.gff3.gz` | `header/conformance/valid/fhgff3-bgzf.fhgff3.gff3.gz` |
| `conformance/valid/fhgff3-both-links.fhgff3.gff3` | `header/conformance/valid/fhgff3-both-links.fhgff3.gff3` |
| `conformance/valid/fhgff3-busco-lineage-dotted.fhgff3.gff3` | `header/conformance/valid/fhgff3-busco-lineage-dotted.fhgff3.gff3` |
| `conformance/valid/fhgff3-crlf.fhgff3.gff3` | `header/conformance/valid/fhgff3-crlf.fhgff3.gff3` |
| `conformance/valid/fhgff3-directives-after-header.fhgff3.gff3` | `header/conformance/valid/fhgff3-directives-after-header.fhgff3.gff3` |
| `conformance/valid/fhgff3-directives-interleaved.fhgff3.gff3` | `header/conformance/valid/fhgff3-directives-interleaved.fhgff3.gff3` |
| `conformance/valid/fhgff3-embedded-fasta.fhgff3.gff3` | `header/conformance/valid/fhgff3-embedded-fasta.fhgff3.gff3` |
| `conformance/valid/fhgff3-extension-fields.fhgff3.gff3` | `header/conformance/valid/fhgff3-extension-fields.fhgff3.gff3` |
| `conformance/valid/fhgff3-gzip.fhgff3.gff3.gz` | `header/conformance/valid/fhgff3-gzip.fhgff3.gff3.gz` |
| `conformance/valid/fhgff3-header-only.fhgff3.gff3` | `header/conformance/valid/fhgff3-header-only.fhgff3.gff3` |
| `conformance/valid/fhgff3-minimal-checksum-link.fhgff3.gff3` | `header/conformance/valid/fhgff3-minimal-checksum-link.fhgff3.gff3` |
| `conformance/valid/fhgff3-minimal-reference-link.fhgff3.gff3` | `header/conformance/valid/fhgff3-minimal-reference-link.fhgff3.gff3` |
| `conformance/valid/fhgff3-nested-parent-checksum.fhgff3.gff3` | `header/conformance/valid/fhgff3-nested-parent-checksum.fhgff3.gff3` |
| `conformance/valid/fhgff3-schema-canonical-raw-main.fhgff3.gff3` | `header/conformance/valid/fhgff3-schema-canonical-raw-main.fhgff3.gff3` |
| `conformance/valid/fhgff3-schema-raw-main.fhgff3.gff3` | `header/conformance/valid/fhgff3-schema-raw-main.fhgff3.gff3` |
| `conformance/valid/fhgff3-triple-hash-before-features.fhgff3.gff3` | `header/conformance/valid/fhgff3-triple-hash-before-features.fhgff3.gff3` |
| `conformance/valid/fhgff3-version-3-1-26.fhgff3.gff3` | `header/conformance/valid/fhgff3-version-3-1-26.fhgff3.gff3` |
| `conformance/valid/fhgff3-version-3-trailing-whitespace.fhgff3.gff3` | `header/conformance/valid/fhgff3-version-3-trailing-whitespace.fhgff3.gff3` |
| `conformance/invalid/fhgff3-annotates-fhp.fhgff3.gff3` | `header/conformance/invalid/fhgff3-annotates-fhp.fhgff3.gff3` |
| `conformance/invalid/fhgff3-busco-lineage-trailing-dot.fhgff3.gff3` | `header/conformance/invalid/fhgff3-busco-lineage-trailing-dot.fhgff3.gff3` |
| `conformance/invalid/fhgff3-cites-fhr-schema.fhgff3.gff3` | `header/conformance/invalid/fhgff3-cites-fhr-schema.fhgff3.gff3` |
| `conformance/invalid/fhgff3-concatenated.fhgff3.gff3` | `header/conformance/invalid/fhgff3-concatenated.fhgff3.gff3` |
| `conformance/invalid/fhgff3-extension-nested.fhgff3.gff3` | `header/conformance/invalid/fhgff3-extension-nested.fhgff3.gff3` |
| `conformance/invalid/fhgff3-extension-older-release.fhgff3.gff3` | `header/conformance/invalid/fhgff3-extension-older-release.fhgff3.gff3` |
| `conformance/invalid/fhgff3-extension-older-version.fhgff3.gff3` | `header/conformance/invalid/fhgff3-extension-older-version.fhgff3.gff3` |
| `conformance/invalid/fhgff3-fasta-tampered.fhgff3.gff3` | `header/conformance/invalid/fhgff3-fasta-tampered.fhgff3.gff3` |
| `conformance/invalid/fhgff3-fhr-only-key.fhgff3.gff3` | `header/conformance/invalid/fhgff3-fhr-only-key.fhgff3.gff3` |
| `conformance/invalid/fhgff3-half-reference.fhgff3.gff3` | `header/conformance/invalid/fhgff3-half-reference.fhgff3.gff3` |
| `conformance/invalid/fhgff3-header-after-fasta.fhgff3.gff3` | `header/conformance/invalid/fhgff3-header-after-fasta.fhgff3.gff3` |
| `conformance/invalid/fhgff3-header-after-feature.fhgff3.gff3` | `header/conformance/invalid/fhgff3-header-after-feature.fhgff3.gff3` |
| `conformance/invalid/fhgff3-header-before-version.fhgff3.gff3` | `header/conformance/invalid/fhgff3-header-before-version.fhgff3.gff3` |
| `conformance/invalid/fhgff3-no-genome-link.fhgff3.gff3` | `header/conformance/invalid/fhgff3-no-genome-link.fhgff3.gff3` |
| `conformance/invalid/fhgff3-schema-unknown-release.fhgff3.gff3` | `header/conformance/invalid/fhgff3-schema-unknown-release.fhgff3.gff3` |
| `conformance/invalid/fhgff3-two-annotates.fhgff3.gff3` | `header/conformance/invalid/fhgff3-two-annotates.fhgff3.gff3` |
| `conformance/invalid/fhgff3-two-checksum-lines.fhgff3.gff3` | `header/conformance/invalid/fhgff3-two-checksum-lines.fhgff3.gff3` |
| `conformance/invalid/fhgff3-version-3-1.fhgff3.gff3` | `header/conformance/invalid/fhgff3-version-3-1.fhgff3.gff3` |
| `conformance/invalid/fhgff3-version-30.fhgff3.gff3` | `header/conformance/invalid/fhgff3-version-30.fhgff3.gff3` |
| `conformance/invalid/fhgff3-version-3x.fhgff3.gff3` | `header/conformance/invalid/fhgff3-version-3x.fhgff3.gff3` |

## Imported shared files (recorded, not vendored)

The model imports the shared core, and the vectors depend on the shared manifest
and format rules. These stay in the publication repository; only their pinned
digests are recorded, so the copy does not duplicate the shared authority:

- `schemas/core.yaml`
- `schemas/shared.yaml`
- `conformance/manifest.json`
- `docs/FORMAT.md`

`fhgff3.json` is generated upstream from `fhgff3_linkml.yml` and is deliberately
**not** copied or hand-edited here.

## Checking and updating the pin

```sh
python3 scripts/check_header_parity.py
python3 scripts/check_header_parity.py --upstream /path/to/FAIR-bioHeaders-Specification
```

The check fails on any changed, missing or unlisted file. To move the pin
deliberately:

1. Choose the new `FAIR-bioHeaders-Specification` commit — the commit of the
   current release tag, or a reviewed `main` commit between releases.
2. Re-copy the upstream paths above byte-for-byte (do not edit them in place).
3. Recompute every size and SHA-256 digest in `header/provenance.json`.
4. Run `scripts/check_header_parity.py --upstream <checkout>` until it passes.
5. Note any schema-contract impact in the pull request. A schema addition or
   changed meaning follows its own review cycle and is not a parity update.

## Licensing

The copied files come from the MPL-2.0 shared publication repository. This
repository's `LICENSE` inventory does not yet enumerate the header tree;
maintainers should add it when merging. The inherited biodatamodels/gff-schema
feature model is excluded from that grant and its upstream permissions remain
unresolved
([FAIR-bioHeaders/FHGFF3#3](https://github.com/FAIR-bioHeaders/FHGFF3/issues/3));
no file here comes from it. Historical notices are preserved unchanged.
