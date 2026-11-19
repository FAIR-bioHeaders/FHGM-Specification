# FHGM continuous integration

FHGM retains the inherited FHGFF3 baseline checks described below and adds one
draft-contract lane. The baseline checks verify the pinned FHGFF3 reference and
its existing fixtures; they do not validate an FHGM contract. The
**FHGM draft model conformance** workflow added with FHGM #9 does run the model
checks — the [conformance manifest](../development/conformance/README.md) across
its available layers, the v0.1 draft self-test, and an offline byte/digest
lane — against the base schema pinned in
[`development/conformance/provenance.json`](../development/conformance/provenance.json).
It grants nothing: FHGM is unreleased, no registry row or schema URL is created,
and selection rule V7 keeps the draft out of every release form. Owned
documentation includes `development/**/*.md`. No feature-model generation or
deployment lane is enabled.

The [declared-reference advisory](reference-advisory.md) additionally checks this
repository's actual external declarations through the immutable central checker.
It is read-only and never repins; live findings run on schedule/manual dispatch.

## Inherited FHGFF3 baseline

The independently authored header and the inherited feature model have separate
validation boundaries. This implements the remaining CI scope in
[issue #8](https://github.com/FAIR-bioHeaders/FHGFF3/issues/8), following the
[October 22 audit](https://github.com/FAIR-bioHeaders/FHGFF3/issues/8#issuecomment-6343246049).

## Jobs and local commands

| Stable job name | Local equivalent | Evidence |
| --- | --- | --- |
| Documentation lint and local links | `npx markdownlint-cli2@0.23.2 --config .markdownlint-cli2.jsonc` then `python3 scripts/check_docs.py` | Owned Markdown lint, existing local file targets, whitespace and conflict markers |
| Header parity and typed microdata fixtures | `python3 -m unittest discover -s tests -v` then `python3 scripts/check_header_parity.py --upstream ../FAIR-bioHeaders-Specification` | Parity failure tests, typed microdata positive/rejection tests, and exact pinned source bytes |
| Pinned shared header conformance | Commands below, in a disposable pinned shared checkout | Shared generated vectors, independent checksums and released toolkit acceptance/rejection |
| Vector bytes, digests and manifest (standard library only) | `python3 development/conformance/run_conformance.py --offline` then `python3 -m unittest discover -s tests -p test_fhgm_conformance.py -v` | Recorded provenance against the tree, per-vector size/SHA-256, independently recomputed file-bound checksums, manifest self-consistency; no third-party import |
| Base, checksum, GFF3 and model layers on the recorded vectors | `python3 development/conformance/run_conformance.py --base-schema <pinned fhgff3.json> --base-schema <second pinned release> --gff3-validate <gff3-validate> --matrix --report-json evidence.json --verbose`, plus `python3 development/model/check_draft.py <pinned fhgff3.json>` | 92 draft FHGM vectors across four separately reported layers, byte regeneration, the v0.1 self-test matrix, and the suite tests against the installed toolkit |
| Downstream draft pins still point at these bytes | `python3 development/conformance/run_conformance.py --offline --check-downstream-pins` | Scheduled/manual only: compares each consumer's recorded sha256 with the contract bytes on `main`. A failure means a pin needs refreshing in the consumer repository; it does not invalidate this repository's vectors |
| External documentation links | `lychee --config ci/lychee.toml --no-progress $(python3 scripts/check_docs.py --list)` | Scheduled/manual HTTP checks; failures remain failures |

CI uses Ubuntu 24.04, Python 3.13 and Node 24. Actions are pinned to commits;
markdownlint-cli2 is pinned to 0.23.2 and Lychee to 0.24.2. The conformance toolkit baseline
is the shared suite's fair-bioheaders 0.8.1 release, with its JSON-LD extra.
The FHGM model lane is a **separate, explicitly selected environment**: the
recorded vector outcomes were observed with fair-bioheaders 0.11.0 and jsonschema
(see `observedWith` in `development/conformance/provenance.json`), the GFF3 feature
layer runs in a second venv with `gff3-validator==0.1.0` installed **without** its
`headers` extra, because that extra pins `fair-bioheaders >=0.4,<0.5` and would
downgrade the environment the checker runs in. `check_draft.py` additionally
passes with 0.8.1, so no recorded outcome depends on a toolkit newer than the
baseline above. Transitive package dependencies resolve from those releases'
declared constraints; this is a released-version baseline, not a fully
hash-locked environment.

Three workflows run on all PRs targeting `main` and pushes to `main`, with no
path-filtered pending checks. All allow manual dispatch. Permissions are read-only,
checkout credentials are not persisted, and every job has a timeout. External
links and the downstream pin-freshness lane run on their schedules and manual
dispatch only; their absence on a PR means **not run**, not verified. Branch
protection remains a maintainer decision after actual workflow results are
available.

## Owned documentation scope

The positive path list in `.markdownlint-cli2.jsonc` is shared by lint, the Python
checker and external links. It covers the root guidance, contribution instructions,
changelog, hand-written microdata proposal, CI guide, fixture provenance and local
header landing pages. Add new owned documentation there. The local checker checks
file targets, including reference definitions, but does not render Markdown or
validate fragment identifiers. Code samples are excluded from link checks.

Inherited/generated documentation and the pinned `header/docs/FHGFF3.md` are outside
that scope: lint must not rewrite either. The pinned document's upstream-relative
links are mapped in [the local landing page](../header/docs/README.md). Its bytes
remain covered by parity. This is not whole-repository link coverage.

External checks use `ci/lychee.toml`, retry transient failures with low concurrency,
and exclude only email verification. The exact 2024 paper DOI is remapped to its
Crossref record because the publisher blocks automated requests. A timeout, 429,
authentication error or unavailable host fails the external job and requires
inspection/retry; none establishes a broken destination or successful verification
by itself. Read the uploaded action summary before interpreting network failures.

## Pinned shared conformance

Use a disposable checkout of FAIR-bioHeaders-Specification at `source.commit` in
[`header/provenance.json`](../header/provenance.json), not current shared main.
From that checkout, run the same commands as CI:

```sh
python3 scripts/check_conformance.py
python3 -m venv /tmp/fhgff3-converter
/tmp/fhgff3-converter/bin/python -m pip install 'fair-bioheaders[jsonld]==0.8.1'
python3 scripts/check_conformance.py --skip-regeneration --require-format jsonld --require-format fhp-fasta --require-format fhgff3 --converter /tmp/fhgff3-converter
```

The existing shared suite checks all its formats, including the FHGFF3 vectors
copied here: version directive ordering, sequence-region interleaving, header
termination, ordinary comments, embedded FASTA, CRLF, nested versus root checksum
coverage, tampering, and the checksum/accession-plus-SeqCol alternatives. Unsupported
required formats fail instead of being silently skipped. Reusing its generator,
manifest and checker avoids a second parser or conformance authority.

Generation, LinkML equivalence, schema drift, version registry and example-schema
validation remain the shared publication repository's checks. This repository has
adopted a byte-exact mirror with recorded imports, not a second build pipeline.
Parity therefore supersedes **local** schema generation/drift baselines proposed
before the layout was adopted. Moving the pin still needs the shared checks and
explicit contract review; a passing parity job alone does not establish a valid new
schema. The microdata tests remain test-only binding fixtures, not runtime support.

Feature validity, header validity, file checksums and parent verification are
different outcomes. This CI does not claim an optional gff3-validator integration
lane or parent-link verification. Those remain with the toolkit and validator's
own suites; plain header-free GFF3 remains usable independently.

## Inherited model boundary and open tracker

No job runs `make`, generates or republishes inherited artifacts. The separate
inherited-model lane is **not enabled**, pending
[licensing evidence in #3](https://github.com/FAIR-bioHeaders/FHGFF3/issues/3).
The upstream request is still awaiting clarification as of October 24, 2026;
our MPL contribution notice is not an upstream grant. An enabled inherited lane
would need an explicit reuse decision, generator pins and a disposable build tree.
`make test` generates/stages artifacts, and `make clean` removes tracked docs.

Completing #8 does not complete the parent
[header tracker #2](https://github.com/FAIR-bioHeaders/FHGFF3/issues/2): its licensing
child remains open. No schema, fixture bytes, license grants or releases change
as part of these CI checks.
