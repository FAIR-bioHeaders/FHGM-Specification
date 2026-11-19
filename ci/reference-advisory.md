# Declared reference advisory

The scheduled/manual `reference-advisory.yml` workflow implements this owning
repository's part of shared
[#241](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/241).
It reports on existing declarations without changing any contract, carrier,
suite, header-copy or consumer pin. It establishes neither FHGM publication nor
curator acceptance.

## Current declarations and independent authority

The adapter reads current local source records each time; it does not reuse a
stale central snapshot of this repository:

| Source | Normalized references |
| --- | --- |
| `header/provenance.json` | Complete declared FHGFF3 header copy, its upstream path scope/local exclusions, and each recorded import |
| `development/model/base-schemas.json` | Each released carrier, separately tagged and commit/digest bound |
| `development/conformance/provenance.json` | Both suite carrier declarations, separately retained and cross-checked against the registry claims |

The initial normalization has nine reference groups: one 49-file copy, four
imports and four carrier declarations (two independently recorded claims for
each base). The report distinguishes a performed local comparison from a
record-only import and checks complete source/local sets for the copied header.
An inconsistency in the duplicate carrier claims is retained and reported as a
declaration finding, never silently repaired. The generated inventory records
the source-record SHA-256 values; CI retains inventory and result JSON together.

FHGM's own model/transport/suite artifacts are owning material, not external
contract references. The existing downstream-pin lookups are reports on other
consumers, not upstream contract authorities. Historical examples, inherited
feature-model references and external biological source data are outside this
family contract-reference inventory. Those exclusions do not assert complete
coverage of every URL in the repository.

The implementation itself is independently pinned in `references/checker.json`:
accepted shared commit, script path and SHA-256. The workflow checks out that
commit, and the runner refuses an unexpected checkout HEAD, repository declaration, safe canonical script path, immutable Git blob
or script digest before executing any checker code. Symlink paths are refused.
The verified stdlib-only checker executes with Python isolation (-I), so an
unverified neighboring module or PYTHONPATH cannot shadow its imports. The central engine is not copied here.
Release tags remain independent authorities; no moving main substitutes for
released bytes. This implementation pin is not a contract repin.

## Commands and outcomes

```sh
python -m unittest discover -s tests -p test_reference_audit.py -v
python scripts/reference_audit.py --checker-root /path/to/pinned-shared-checkout \
  --checkout FAIR-bioHeaders/FAIR-bioHeaders-Specification=/path/to/shared-with-tags \
  --exercise-controls --inventory-output /tmp/fhgm-reference-inventory.json \
  --output /tmp/fhgm-reference-offline.json
```

With `--checkout`, all authority resolution is local and missing git objects or
unmapped repositories are query failures. Without it, the verified engine uses
the GitHub API and confirms missing-path controls before interpreting results.
`FRESH`, `DRIFT`, `ABSENT` and `QUERY_FAILED` describe actual measurements;
access/transport failures are not fabricated absence. The audit returns advisory
results even for findings. Invalid implementation pins or execution failures
refuse the run; they cannot establish a successful reference comparison.
Only explicitly requested report artifacts are written, never source records.

The controls use a real temporary git authority with an immutable local fixture
tag. They prove FRESH, a changed-recorded-digest DRIFT, confirmed missing-file
ABSENT and unmapped-authority QUERY_FAILED. The digest mutant must change actual
serialized inventory bytes; the authority bytes must remain untouched.
Adapter tests additionally prove declaration disagreement is not repaired and
unverified implementation code cannot execute, including joint file/digest
tampering. A paired shadow-module control proves the unisolated command would
execute an unverified neighbor while the isolated command does not.

Pull requests exercise the adapter, fixture controls and offline integration.
The live network report runs only on schedule/manual dispatch with read-only
permissions; its findings do not gate contract changes or trigger repinning.
Reports are uploaded as workflow artifacts and live findings are written to the
job summary. A deliberate reviewed commit is required for any future pin move.
