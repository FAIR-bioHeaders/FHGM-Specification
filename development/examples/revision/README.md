# FHGM revision pilot

The [S6k pilot](../s6k/README.md) showed that a single-locus contribution fits
FHGFF3 1.1 with an extension field. This follow-up tests whether a revision can
point to the exact file it proposes to replace and where the base contract
stops checking that claim.

## Published use case

Flanagan, Hund and Chihade describe corrected gene models and provide an
associated dataset covering multiple published assemblies. The article
motivates capturing which model on which assembly is being revised and the
evidence for the change. The deposit's DataCite record links to the article
with `IsPartOf` and to a dataset version family with `IsVersionOf`. Neither
link establishes that a curator adopted a replacement for a specific model.

- [Article](https://doi.org/10.17912/micropub.biology.002355)
- [Dataset](https://doi.org/10.22002/hv4eg-wg213)
- [DataCite record](https://api.datacite.org/dois/10.22002/hv4eg-wg213)

The cases below are synthetic and contain no files, identifiers or sequences
from that study. The original and revision describe one toy noncoding locus
on the same toy assembly. The revision extends its exon and keeps the
feature IDs stable. The assembly SeqCol digest is computed from the synthetic
one-record collection defined in the script.

## Reproduce the comparison

Use Python with PyYAML and jsonschema installed. From this directory, point
the script at the released [FHGFF3 1.1 schema from v0.5.0](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/v0.5.0/fhgff3.json).
The output directory must already exist.

```sh
out=$(mktemp -d)
python3 check_revision.py /path/to/fhgff3.json "$out"
for file in "$out"/*.gff3; do
  gff3-validate --no-header "$file"
  awk '!/^#~checksum:/' "$file" | openssl dgst -sha512-256 -binary | openssl base64 -A
  printf '\n'
  awk '/^#~checksum:/{print $2}' "$file"
done
```

| Case | FHGFF3 1.1 schema | File checksum | Predecessor check |
| --- | --- | --- | --- |
| Original | Pass | Pass | No predecessor claim |
| Revised with experimental extension | Pass | Pass | Matches supplied original checksum, version and assembly |
| Revised with stale predecessor checksum | Pass | Pass | Fails against the supplied original |
| Revised using `derivedFrom.relationship: supersedes` | Rejected at the relationship field | Generated in memory | Outside the base vocabulary |

All three emitted files passed the feature check with zero errors and warnings
using gff3-validator 0.1.0 at `c753f45`, with header checks disabled. OpenSSL
independently reproduced each file checksum.

## Design questions for curator review

The experimental field can carry a precise predecessor pointer while keeping
FHGFF3 schema identity. The stale case shows that schema and checksum validity
cannot establish whether that pointer resolves. Even a resolved pointer does
not establish that a curator accepted the revision.

Before standardizing a field, decide who can declare supersession, what source
records that decision, and whether the target is an entire contribution file
or a particular model within a larger annotation. Ask whether a correction
on a different assembly is a replacement, a new contribution or an assembly
mapping. Keep the publication, deposit version, exact predecessor file and
curation decision separately identifiable.
