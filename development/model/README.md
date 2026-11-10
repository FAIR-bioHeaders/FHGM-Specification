# Draft FHGM validation

This proposed schema addition defines the contents of `x-fhgm-models` on a
released FHGFF3 1.1 file. Run the base schema and the overlay together. The
overlay is selected explicitly by running this validator. The file retains
its original FHGFF3 schema URI and version, including the base assembly
requirement and exact-byte checksum rule.

| Field | Cardinality | Meaning |
| --- | --- | --- |
| `x-fhgm-models` | One or more records | Model contributions described by the annotation snapshot. |
| `modelId` | One | Opaque model identifier, unique within the snapshot and stable across a revision. |
| `modelVersion` | One | Opaque version string. A revision must use a different value from its predecessor. |
| `featureId` | One | Exact, decoded local GFF3 ID resolving to one `gene` row. Isoforms remain in the GFF3 feature graph. |
| `predecessor` | Zero or one | Prior annotation checksum, model ID and model version for an immediate same-assembly revision. |
| `contributors` | Optional nonempty list | Supplied names and model contribution roles. File metadata authors remain in `metadataAuthor`. |
| `evidence` | Optional nonempty list | Supplied model evidence descriptions. Article and dataset identifiers retain their separate FHGFF3 roles. |

For a revision, supply the predecessor file explicitly. Both snapshots must
pass the schema, checksum and target checks. The validator requires a common
assembly identifier form (an FHR checksum or the accession and SeqCol pair)
and rejects conflicts between shared identifiers. It checks the immediate
pointer. Curator acceptance, transitive history, split and merge, assembly
migration, transcript-only scope, and structured evidence identifiers remain
review topics.

Use Python with `fair-bioheaders` (the draft reuses its GFF3 header reader
and checksum implementation) and `jsonschema`. From the FHGM repository root,
with a local checkout of the shared specification:

```sh
git -C /path/to/FAIR-bioHeaders-Specification show v0.5.0:fhgff3.json > /tmp/fhgff3-v0.5.0.json
python development/model/validate_fhgm.py --base-schema /tmp/fhgff3-v0.5.0.json \
  --predecessor development/examples/contract/minimal.fhgff3.gff3 \
  development/examples/contract/rich.fhgff3.gff3
python development/model/check_draft.py /tmp/fhgff3-v0.5.0.json
```

Run `gff3-validate --no-header` separately for GFF3 syntax and feature graph
checks. Reference sequence matching and biological evidence assessment
require their own inputs. See the [INSDC supplement](../INSDC-COVERAGE.md)
for the coverage boundary.
