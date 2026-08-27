#!/usr/bin/env python3
"""Offline smoke checks for Biopython sequence objects and features.

The checks use only in-memory data and require only an importable Biopython
installation. They intentionally avoid file parsing, network calls, databases,
and external executables.
"""

from __future__ import annotations

from Bio.Data.CodonTable import TranslationError
from Bio.Seq import MutableSeq, Seq, back_transcribe, reverse_complement, transcribe
from Bio.SeqFeature import CompoundLocation, SeqFeature, SimpleLocation
from Bio.SeqRecord import SeqRecord
from Bio.SeqUtils import gc_fraction, molecular_weight, nt_search, seq1, seq3


def diagnose_cds_translation(feature: SeqFeature, parent_sequence: Seq) -> dict[str, object]:
    """Return compact diagnostics for complete-CDS translation failures."""
    extracted = feature.extract(parent_sequence)
    table = feature.qualifiers.get("transl_table", ["Standard"])[0]
    codon_start = int(feature.qualifiers.get("codon_start", [1])[0])
    offset = codon_start - 1
    coding = extracted[offset:]
    info: dict[str, object] = {
        "table": table,
        "codon_start": codon_start,
        "start_offset": offset,
        "length": len(coding),
        "length_mod_3": len(coding) % 3,
        "first_codon": str(coding[:3]),
        "final_codon": str(coding[-3:]) if len(coding) >= 3 else str(coding),
    }
    try:
        info["translation"] = str(feature.translate(parent_sequence))
    except TranslationError as err:
        info["error"] = str(err)
    return info


def main() -> None:
    # Seq and MutableSeq biological methods.
    dna = Seq("ATGGCC")
    assert str(dna.translate()) == "MA"
    assert str(dna.reverse_complement()) == "GGCCAT"
    assert transcribe("ATGGCC") == "AUGGCC"
    assert back_transcribe("AUGGCC") == "ATGGCC"
    assert reverse_complement("ATGGCC") == "GGCCAT"

    mutable = MutableSeq("ATGGCC")
    mutable.reverse_complement(inplace=True)
    assert str(mutable) == "GGCCAT"

    # SeqRecord annotations, per-letter annotations, slicing, and features.
    record = SeqRecord(
        Seq("ATGAAATTTCCCTAAGGGGG"),
        id="toy",
        name="toy_record",
        description="in-memory circular test record",
        annotations={"molecule_type": "DNA", "topology": "circular"},
    )
    record.letter_annotations["quality"] = list(range(len(record)))

    cds_feature = SeqFeature(
        SimpleLocation(0, 9, strand=1) + SimpleLocation(12, 15, strand=1),
        type="CDS",
        qualifiers={"gene": ["toyA"], "codon_start": ["1"], "transl_table": [1]},
    )
    origin_feature = SeqFeature(
        CompoundLocation([SimpleLocation(15, 20, strand=1), SimpleLocation(0, 3, strand=1)]),
        type="misc_feature",
        qualifiers={"note": ["origin-spanning toy feature"]},
    )
    record.features.extend([cds_feature, origin_feature])

    assert str(cds_feature.extract(record.seq)) == "ATGAAATTTTAA"
    assert str(cds_feature.translate(record.seq)) == "MKF"

    extracted_record = cds_feature.extract(record)
    assert isinstance(extracted_record, SeqRecord)
    assert str(extracted_record.seq) == "ATGAAATTTTAA"

    cds_slice = record[:15]
    assert cds_slice.annotations == {"molecule_type": "DNA"}
    assert cds_slice.letter_annotations["quality"] == list(range(15))
    assert len(cds_slice.features) == 1
    assert str(cds_slice.features[0].extract(cds_slice.seq)) == "ATGAAATTTTAA"

    # Difficult case: feature wrapped across the origin of a circular sequence.
    assert record.annotations["topology"] == "circular"
    assert str(origin_feature.extract(record.seq)) == "GGGGGATG"
    assert list(origin_feature.location) == [15, 16, 17, 18, 19, 0, 1, 2]
    assert origin_feature.location.start == 0
    assert origin_feature.location.end == len(record)

    # Reverse-complementing a record flips feature coordinates and reverses per-letter data.
    rc_record = record.reverse_complement(id=True, name=True, description=True, annotations=True)
    assert str(rc_record.seq) == str(record.seq.reverse_complement())
    assert rc_record.id == record.id
    assert rc_record.annotations["molecule_type"] == "DNA"
    assert rc_record.letter_annotations["quality"] == list(reversed(range(len(record))))
    assert len(rc_record.features) == len(record.features)

    # SeqUtils functions.
    assert gc_fraction("ACTGN", ambiguous="weighted") == 0.5
    assert round(molecular_weight("AGC", seq_type="DNA"), 2) == 949.61
    assert nt_search("ATGCAT", "ATN")[1:] == [0]
    assert seq1(seq3("MAIVMGR*")) == "MAIVMGR*"

    # Difficult case: diagnose a complete-CDS translation failure.
    bad_parent = Seq("ATGAAAACGT")
    bad_cds = SeqFeature(SimpleLocation(0, len(bad_parent), strand=1), type="CDS")
    diagnosis = diagnose_cds_translation(bad_cds, bad_parent)
    assert "multiple of three" in str(diagnosis["error"])
    assert diagnosis["first_codon"] == "ATG"
    assert diagnosis["length"] == 10
    assert diagnosis["length_mod_3"] == 1

    print("PASS")


if __name__ == "__main__":
    main()
