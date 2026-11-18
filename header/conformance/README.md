# FHGFF3 conformance vectors

These are the `fhgff3` conformance vectors — GFF3 files carrying an FHGFF3
`#~` header — copied byte-for-byte from the shared publication repository at the
pinned revision recorded in [`../provenance.json`](../provenance.json).

- `valid/`: files a conforming FHGFF3 reader must accept (18 files).
- `invalid/`: files it must reject (20 files).
- `*.gz`: gzip/BGZF copies; validate their decompressed bytes.

The authoritative manifest, the generator (`scripts/make_conformance.py`) and the
checker (`scripts/check_conformance.py`) live in the publication repository and
are **not** duplicated here:

- <https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/conformance/README.md>
- <https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/conformance/manifest.json>

The expected outcome, rules and descriptions for these files are the
`format: "fhgff3"` entries of that manifest. The rules G1–G3 are defined in
`docs/FHGFF3.md`, the shared FORMAT rules these vectors cite (R1–R4, R7, R10
and R15) in `docs/FORMAT.md`, and the selection rules (V1, V4) in
`docs/SCHEMA-VERSIONS.md`. Do not hand-edit these files or
re-save them in an editor: they are byte-exact, and the `.gitattributes` at the
repository root disables line-ending conversion for `header/**`.

Regenerate vectors in the shared repository, then re-import and update
`header/provenance.json` as described in [`../PROVENANCE.md`](../PROVENANCE.md).
