# Contributing to FHGM

FHGM is in requirements gathering. Track work through
[the family proposal #204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
and link each scoped PR to it. The fork currently has issues disabled; use the
shared issue until maintainers establish local tracking.

## Active development

Work in [development/](development/README.md). Start with real deposited GFF3
files and compare requirements against the FHGFF3 baseline. Keep header fields,
feature constraints, evidence assertions and validation outcomes distinct.
Do not invent identifiers, provenance, permissions or biological relationships.

New fields, constraints, requiredness or changed meanings are schema-contract work.
State compatibility effects explicitly. No FHGM schema URL, version or support is
adopted by this scaffold. David and Adam review the contract before publication
through the shared specification. Submit branches and PRs; do not push directly
to main or merge without maintainer approval.

## Preserved reference material

Do not edit pinned files in `header/` to implement FHGM: parity deliberately checks
FHGFF3 source bytes. Record any future base update separately, following
[header/PROVENANCE.md](header/PROVENANCE.md). Use a separate draft model path once
the contract design is agreed; define its generator/import strategy then.

The inherited feature model lives in `src/schema/gff.yaml` with generated outputs
elsewhere. Its upstream permissions remain unresolved. Do not generate or reuse
it as FHGM implementation until that boundary is resolved. The inherited Makefile
is not an FHGM build: `make test` generates/stages and `make clean` removes docs.

## Checks

Run the commands in [ci/README.md](ci/README.md). Add new owned Markdown to
`.markdownlint-cli2.jsonc` so lint and local-link checks cover it. Baseline tests
prove only the properties described by their existing fixtures; they do not
validate FHGM records. Record checks actually run and any environment limitations.

## Contribution licensing

New FHGM guidance under `development/` and the FHGM setup portions identified in
[LICENSE](LICENSE) use MPL-2.0. Preserve inherited notices and attribution. This
license does not resolve permissions for the inherited gff-schema tree or for
article-associated deposits; inspect those sources individually.

## Review and merge handoff

Every PR receives independent review from another actual model, preferably from
a different family. Record author and reviewer identities. Agents fix failing CI
and actionable overall/inline reviews and hand the validated current head to a
human. Only humans merge; agents never merge, enable auto-merge, queue a merge,
use a merge proxy or push a default branch as a substitute. See
[AGENTS.md](AGENTS.md) for the current policy and review dispositions.
