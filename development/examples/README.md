# Worked-example preparation

Select public contributions from the
[microPublication Biology Gene Models collection](https://www.micropublication.org/journals/biology/collections/genemodels/).
The initial candidate in
[issue #204](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/204)
is not yet an approved fixture. No FHGM examples have been created or validated.

See [the pilot source review](PILOT.md) for the initial archive findings and
publication context.

For each candidate, copy [SOURCE-TEMPLATE.md](SOURCE-TEMPLATE.md) to a descriptive
case directory as `SOURCE.md`. Complete the source review before adding payloads.
Cover a new model, a revision, multiple isoforms and a noncoding case where available.

Record article and deposit identifiers separately, actual filenames/formats,
retrieval dates, source versions, reuse permissions and unmodified source hashes.
Extract metadata with evidence for each value. Unknown optional values remain
absent; unavailable required information becomes a design question.

Keep original payload bytes and any derived file distinct, documenting every
transformation. Do not write FH checksums by hand or label ordinary source hashes
as FH checksums. Add headed FHGM examples only after draft payload/schema selection
and explicit tooling support exist. Mark synthetic fixtures clearly.
