# SPDX-License-Identifier: MPL-2.0
"""Generate the draft FHGM conformance vectors deterministically.

Companion generator to ``development/examples/model/make_fixtures.py``: it reuses
that pilot's machinery — the ``check_revision`` render helpers, the synthetic
one-record SeqCol collection and the synthetic assembly — so every vector here is
byte-reproducible with ``cmp`` and cites no external payload. All content is
synthetic; the accessions, model IDs, URNs and evidence strings are placeholders
scoped to this directory.

Two rules govern what this file may emit.

* A vector's expected outcome must be **observed** by running
  ``development/model/validate_fhgm.py`` on the emitted bytes before it is
  recorded: ``run_conformance.py --seal`` builds the manifest from real checker
  runs, and the committed manifest is then verified, never edited by hand.
* Nothing here gives semantics to split, merge, assembly migration,
  transcript-only contribution or companion-file identity. Those are #204 open
  question Q6, left to curators; the manifest records them as open scope with no
  vectors. A rejection that looks like one of them (the transcript-target vector)
  is labelled as a statement about v0.1's scope only.

Usage: ``python3 make_vectors.py <existing-directory>`` writes
``vectors/valid/`` and ``vectors/invalid/`` under that directory. The runner
regenerates into a temporary directory and compares bytes.
"""

import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "examples" / "revision"))
from check_revision import (  # noqa: E402
    MODELS,
    checksum,
    feature_payload,
    render,
    synthetic_reference,
)

# The ambiguous snapshot whose modelId collides is the committed v0.1 fixture, so
# the vector that points at it reads that file's own checksum line rather than a
# transcribed digest.
FIXTURES = HERE.parents[0] / "examples" / "model"
AMBIGUOUS_SNAPSHOT = FIXTURES / "ambiguous-model-id.fhgff3.gff3"

DATE = "2026-11-14"
AUTHOR = "FHGM conformance vector generator (synthetic)"
REFERENCE = synthetic_reference()
# A synthetic FHR parent binding: the digest is computed over declared synthetic
# bytes, so it is reproducible and is not presented as the checksum of any real
# file.
FHR_PARENT_CHECKSUM = checksum(b"synthetic FHGM conformance FHR parent bytes\n")


def metadata(models, file_version, genome_link=True, **extra):
    header = {
        "schema": "https://w3id.org/fair-bioheaders/fhgff3/v0.5.0",
        "schemaVersion": "1.1",
        "annotation": "Synthetic annotation for the draft FHGM conformance vectors",
        "taxon": {"name": "Synthetic example"},
        "metadataAuthor": [{"name": AUTHOR}],
        "dateCreated": DATE,
        "genomeReference": REFERENCE,
        "version": file_version,
        MODELS: models,
    }
    header.update(extra)
    if not genome_link:
        del header["genomeReference"]
    return header


def fhr_parent_link():
    return {
        "derivedFrom": [
            {
                "headerType": "FHR",
                "checksum": FHR_PARENT_CHECKSUM,
                "relationship": "annotates",
            }
        ]
    }


def record(model_id, model_version, feature="toy-a", **extra):
    model = {
        "modelId": model_id,
        "modelVersion": model_version,
        "featureId": feature,
        "reference": {"genomeReference": REFERENCE},
    }
    model.update(extra)
    return model


def pointer(annotation_checksum, model_id, model_version):
    return {
        "annotationChecksum": annotation_checksum,
        "modelId": model_id,
        "modelVersion": model_version,
    }


def header_checksum(data):
    for line in data.splitlines():
        if line.startswith(b"#~checksum: "):
            return line[len(b"#~checksum: "):].decode()
    raise AssertionError("vector input has no checksum line")


def valid_vectors():
    """Vectors the released base schema and the model-level checker accept."""
    return {
        # Disposition Q2: file-local identity is the default and needs no minting
        # authority, and a producer-supplied external identifier may occupy the
        # same opaque field. The urn:example: namespace is reserved for
        # documentation, so this claims no registry.
        "supplied-external-model-id": render(
            metadata([record("urn:example:gene-model-7", "deposit-v1")], "1"),
            feature_payload(30),
        ),
        # Rule K5 with the file carrying both released FHGFF3 genome-link forms:
        # one record binds the FHR parent checksum, the other the accession plus
        # supplied SeqCol digest, and each shares a comparable form.
        "both-reference-forms": render(
            metadata(
                [
                    record("model-a", "1", reference={"annotates": FHR_PARENT_CHECKSUM}),
                    record("model-b", "1", feature="toy-b"),
                ],
                "1",
                **fhr_parent_link(),
            ),
            feature_payload(30),
        ),
        # The other FHGFF3 genome-link branch at file scope, with a record bound
        # the same way: no v0.1 fixture used a derivedFrom-only link.
        "file-linked-by-fhr-parent": render(
            metadata(
                [record("model-a", "1", reference={"annotates": FHR_PARENT_CHECKSUM})],
                "1",
                genome_link=False,
                **fhr_parent_link(),
            ),
            feature_payload(30),
        ),
        # Rule K4 compares the percent-decoded feature ID with the record.
        "percent-decoded-feature-target": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30).replace(b"ID=toy-a\n", b"ID=toy%2Da\n"),
        ),
        # Rule K1, base selection by citation: the v0.6.0 release accepts a
        # record stating schemaVersion 1.1 (shared docs/SCHEMA-VERSIONS.md), so
        # the checker selects the v0.6.0 bytes the URL cites and the overlay's
        # v0.6.0 branch admits 1.1.
        "v0.6.0-citation-stating-1.1": render(
            dict(metadata([record("model-a", "1")], "1"),
                 schema="https://w3id.org/fair-bioheaders/fhgff3/v0.6.0"),
            feature_payload(30),
        ),
        # Rule K1: the raw tag URL under the FHR-Specification alias is the
        # same v0.6.0 release (both repository names are recognised). Its 1.2
        # twin keeps this citation, so the alias is exercised under both
        # stated versions.
        "fhr-specification-alias-v0.6.0": render(
            dict(metadata([record("model-a", "1")], "1"),
                 schema="https://raw.githubusercontent.com/FAIR-bioHeaders/"
                        "FHR-Specification/v0.6.0/fhgff3.json"),
            feature_payload(30),
        ),
    }


def invalid_vectors():
    """Vectors the model-level checker rejects (or the base schema, where noted)."""
    ambiguous_checksum = header_checksum(AMBIGUOUS_SNAPSHOT.read_bytes())
    return {
        # Rule K2: nested objects are closed. The base schema ignores record
        # contents, so only the record contract can reject this (FORMAT.md R15
        # grants top-level x- keys only, never keys inside a record).
        "record-unknown-key": render(
            metadata([record("model-a", "1", unexpected="synthetic")], "1"),
            feature_payload(30),
        ),
        # Rule K2: modelVersion is an opaque non-empty string, not a number.
        "record-numeric-model-version": render(
            metadata([dict(record("model-a", "1"), modelVersion=2)], "1"),
            feature_payload(30),
        ),
        # Rule K1: the transport array must hold at least one record.
        "empty-model-array": render(metadata([], "1"), feature_payload(30)),
        # Rule K1: FORMAT.md R15 grants extension keys from FHGFF3 1.1 only. This
        # is the one vector the released base schema itself rejects.
        "transport-1-0-extension": render(
            dict(
                metadata([record("model-a", "1")], "1"),
                schema="https://w3id.org/fair-bioheaders/fhgff3/v0.4.0",
                schemaVersion="1.0",
            ),
            feature_payload(30),
        ),
        # Rule K5, the stronger half: nothing contradicts, and the record is still
        # rejected for sharing no comparable form with the file genome link. This
        # is the behaviour the adoption packet's D1 summary under-describes.
        "reference-forms-not-comparable": render(
            metadata([record("model-a", "1", reference={"annotates": FHR_PARENT_CHECKSUM})], "1"),
            feature_payload(30),
        ),
        # Rule K3 reached through the pointer side: the supplied prior snapshot is
        # itself ambiguous, so loading it rejects the run before any verdict for
        # this record's pointer is reported (deviation D4 at snapshot level).
        "pointer-into-ambiguous-history": render(
            metadata(
                [record("model-a", "2", predecessor=pointer(ambiguous_checksum, "model-a", "1"))],
                "2",
            ),
            feature_payload(35),
        ),
        # Rule K4: the target resolves to no local row.
        "feature-target-absent": render(
            metadata([record("model-a", "1", feature="toy-missing")], "1"),
            feature_payload(30),
        ),
        # Rule K4: a transcript row is not a gene row. This is a statement about
        # v0.1 scope only; #204 Q6 leaves transcript-only contribution open.
        "feature-target-transcript-row": render(
            metadata([record("model-a", "1", feature="toy-a-rna")], "1"),
            feature_payload(30),
        ),
        # Rule K4: exactly one row, not two rows sharing the ID.
        "feature-target-duplicate-rows": render(
            metadata([record("model-a", "1")], "1"),
            feature_payload(30) + b"toy\tpilot\tgene\t1\t5\t.\t+\t.\tID=toy-a\n",
        ),
        # The R15 floor under a registered citation: the v0.5.0 URL stating
        # schemaVersion 1.0. The checker selects the v0.5.0 bytes the URL cites,
        # and those bytes reject the extension key. transport-1-0-extension
        # cites v0.4.0, which no registered base answers to, so it is refused
        # at selection instead; this vector keeps the floor itself observed.
        "transport-1-0-under-v0.5.0-citation": render(
            dict(metadata([record("model-a", "1")], "1"), schemaVersion="1.0"),
            feature_payload(30),
        ),
        # Rule K1, base selection by citation: raw main is a moving contract
        # link, not a release, so no registered base answers to it and the
        # checker refuses rather than evaluating the carrier against bytes it
        # never cited. The released base schema's URL pattern accepts it.
        "carrier-cites-raw-main": render(
            dict(metadata([record("model-a", "1")], "1"),
                 schema="https://raw.githubusercontent.com/FAIR-bioHeaders/"
                        "FAIR-bioHeaders-Specification/main/fhgff3.json"),
            feature_payload(30),
        ),
        # Integrity, not a model rule: one byte added after the header makes the
        # file-bound checksum stop covering the file, so the checker refuses
        # before any model verdict. Recorded with checksum outcome "stale", and
        # the one vector this suite does not claim as gap-proof.
        "tampered-record-bytes":
            (FIXTURES / "valid-single.fhgff3.gff3").read_bytes()
            + b"# byte added after the header\n",
    }


def run(output):
    written = 0
    for kind, vectors in (("valid", valid_vectors()), ("invalid", invalid_vectors())):
        target = output / "vectors" / kind
        target.mkdir(parents=True, exist_ok=True)
        for name, data in sorted(vectors.items()):
            path = target / f"{name}.fhgff3.gff3"
            path.write_bytes(data)
            print(f"vectors/{kind}/{name}.fhgff3.gff3  {checksum(path.read_bytes())}")
            written += 1
    if written != len(valid_vectors()) + len(invalid_vectors()):
        raise AssertionError("vector count changed under construction")
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Existing directory for the vectors")
    args = parser.parse_args()
    run(args.output)
