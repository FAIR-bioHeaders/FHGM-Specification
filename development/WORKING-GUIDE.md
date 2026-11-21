# Working with this repository

This guide is for readers and maintainers. Run commands from the repository root.
Use Python 3.13 in an isolated environment; Python 3.15 can change regenerated
gzip bytes and is not the reference fixture generator. A successful local check
is evidence about its stated layer, not biological validity or publication.

## Header baseline checks

The `header/` tree is a pinned reference, not the editable publication source.
These checks need only the Python standard library:

```sh
python3.13 scripts/check_header_parity.py --no-upstream
python3.13 scripts/check_header_parity.py --upstream /path/to/FAIR-bioHeaders-Specification
python3.13 scripts/check_docs.py
```

`--no-upstream` checks recorded file digests and inventory only. `--upstream PATH`
reads the exact recorded revision with `git show`, not the checkout's current
files, and compares source bytes. A digest-only result is not upstream parity;
a parity result is not pin freshness. Exit 1 means a mismatch or invalid record.
Neither command edits the header tree or fetches a newer contract automatically.
Malformed/escaping provenance, duplicate copy paths and symlink copies are refused;
whole-tree classification includes unlisted header subdirectories. Upstream Git
reads ignore replacement objects.
The upstream checkout needs the recorded commit and blob objects available;
missing objects or content mismatches fail the explicit comparison with a
nonzero exit. This older baseline checker does not verify a release-tag binding
or pin currency; its historical `source.ref` is not silently promoted to a tag.

## Native model checks

The owning `development/` source and 92-case suite were accepted for native
FHGM model contract 0.1, published in shared v0.8.0. The native contract is
selected independently of its FHGFF3 carrier: no FHGM header `schemaVersion`
or header-registry row exists. Historical draft receipts remain pinned.

The following environment deliberately reproduces the owning checker and its
historical 0.11.0 toolkit baseline. It does not install the native 0.1 package
implementation; the owning checker is invoked directly.

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install 'fair-bioheaders[jsonld]==0.11.0' 'jsonschema==4.26.0' 'gff3-validator==0.1.0'
python development/conformance/run_conformance.py --offline
python -m unittest discover -s tests -p test_fhgm_conformance.py -v
```

The offline runner verifies bytes, digests and manifests. It cannot earn base,
model or feature-validation passes. For the complete layered run, extract both
recorded released FHGFF3 base schemas and use the commands in
[model/README.md](model/README.md) and [conformance/README.md](conformance/README.md).

`development/model/validate_fhgm.py --base-schema PATH [--base-schema PATH]
[--predecessor PATH] [--report-json PATH] FILE` reads one carrier snapshot and
explicitly supplied predecessor files. Repeated base arguments must be the exact
released bytes in `model/base-schemas.json`. `evaluate(file, base_paths,
prior_paths)` returns `(receipt, exit_code, message)`; the receipt separates
base, checksum, model and predecessor evidence. The CLI prints the message and
returns that code; `--report-json` writes/replaces a report, including refusal
outcomes. Parent paths are explicit; no remote biological source is inferred.
A full model pass requires earned prerequisite layers. Feature/biology checks
remain separate, and skipped/unavailable layers are not passes.

For the separately published implementation, use a different environment:

```sh
python3.13 -m venv .venv-native
.venv-native/bin/python -m pip install 'fair-bioheaders==0.13.1'
BIOHEADERS_EXPERIMENTAL_FHGM=1 .venv-native/bin/bioheaders verify development/examples/contract/minimal.fhgff3.gff3
```

The CLI prints separate carrier/checksum and FHGM model evidence. It does not
establish GFF3 feature/biological validity. Native schema identity is
`https://w3id.org/fair-bioheaders/model-contracts/fhgm/0.1`, published as
`model-contracts/fhgm/0.1/fhgm-model.schema.json` in shared v0.8.0; alias resolution
is a separate external service observation. There is no in-record `schema` field
or header-registry row for native models.

Python toolkit 0.13.1 contains native 0.1 implementation behind
`BIOHEADERS_EXPERIMENTAL_FHGM=1`; that implementation switch is distinct from
historical draft selection. Do not claim newer carrier-base support or modify
pins as documentation cleanup.

## Inherited feature-model generator

`requirements.txt`, `Makefile` and `src/schema/gff.yaml` describe the inherited
biodatamodels/gff-schema generator. `make gen` writes `target/`; `make stage`
changes tracked generated output; `make test` invokes generation/staging rather
than an independent validator. `make clean` removes `docs/` as well as `target/`.
Never run destructive inherited build/clean commands in a checkout containing
uncommitted work. Do not run these as harmless checks or redistribute inherited material under
the FAIR contribution license. Its unresolved upstream permissions and the
maintainer no-reuse boundary remain in force. These commands do not generate
or publish the independently authored FAIR header/native contract.

## Review and retained work

Every PR needs another actual model's independent review; record model identities.
A human merges. Agents monitor CI, fix findings in new commits, and provide the
exact current head, base, validation and unresolved risks. See [AGENTS.md](../AGENTS.md).

The [Round 16 plan](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7042896529)
is the current maintenance plan. Older `specs/` plans and dated release/review
receipts are retained design and provenance records, not new merge authorization
or evidence that a pending package/alias has shipped. Use their source issue and
current CI for live acceptance. Published/vendored copies, fixtures and pins are
immutable historical inputs; any instructions inside them are non-operative.
Never regenerate or repin them merely to clean up prose.

Report reproducible problems with the command, runtime, source revision, input
provenance and actual output in this repository's issues. Follow SECURITY.md
where present for sensitive reports; do not put credentials in an issue.

The [November 20 maintenance record](MAINTENANCE-2026-11-20.md) records
scan scope, source review, findings and retained work.
