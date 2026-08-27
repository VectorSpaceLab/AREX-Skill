#!/usr/bin/env python3
"""Offline smoke checks for Biopython SeqIO, AlignIO, indexing, and conversion."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from Bio import AlignIO, SeqIO, bgzf
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqIO.FastaIO import SimpleFastaParser
from Bio.SeqIO.QualityIO import FastqGeneralIterator
from Bio.SeqRecord import SeqRecord


def make_records() -> list[SeqRecord]:
    records = [
        SeqRecord(Seq("ACGTACGT"), id="alpha", description="alpha example"),
        SeqRecord(Seq("GGGTTTAA"), id="beta", description="beta example"),
    ]
    for record in records:
        record.annotations["molecule_type"] = "DNA"
        record.letter_annotations["phred_quality"] = [40] * len(record)
    return records


def check_seqio(tmp: Path) -> None:
    records = make_records()
    fasta = tmp / "records.fasta"
    fastq = tmp / "records.fastq"
    tab = tmp / "records.tab"
    idx_file = tmp / "records.idx"
    bgzf_fasta = tmp / "records.fasta.bgz"

    assert SeqIO.write(records, fasta, "fasta") == 2
    parsed = list(SeqIO.parse(fasta, "fasta"))
    assert [record.id for record in parsed] == ["alpha", "beta"]
    assert str(parsed[0].seq) == "ACGTACGT"

    try:
        SeqIO.read(fasta, "fasta")
    except ValueError as exc:
        assert "More than one record" in str(exc)
    else:  # pragma: no cover - defensive branch for changed API behavior
        raise AssertionError("SeqIO.read should reject multi-record FASTA")

    first = next(SeqIO.parse(fasta, "fasta"))
    assert first.id == "alpha"

    as_dict = SeqIO.to_dict(SeqIO.parse(fasta, "fasta"))
    assert sorted(as_dict) == ["alpha", "beta"]

    indexed = SeqIO.index(fasta, "fasta")
    try:
        assert indexed["beta"].seq == Seq("GGGTTTAA")
        raw = indexed.get_raw("alpha")
        assert isinstance(raw, bytes)
        assert raw.startswith(b">alpha")
    finally:
        indexed.close()

    db_index = SeqIO.index_db(idx_file, [fasta], "fasta")
    try:
        assert len(db_index) == 2
        assert db_index["alpha"].description == "alpha example"
    finally:
        db_index.close()

    assert SeqIO.write(records, fastq, "fastq") == 2
    assert SeqIO.convert(fastq, "fastq", tab, "tab") == 2
    tab_text = tab.read_text()
    assert "alpha" in tab_text and "ACGTACGT" in tab_text

    with bgzf.open(bgzf_fasta, "wt") as handle:
        assert SeqIO.write(records, handle, "fasta") == 2
    bgzf_index = SeqIO.index(bgzf_fasta, "fasta")
    try:
        assert list(bgzf_index) == ["alpha", "beta"]
        assert bgzf_index["alpha"].seq == Seq("ACGTACGT")
    finally:
        bgzf_index.close()


def check_low_level_iterators() -> None:
    fasta_text = ">alpha first sequence\nACGT\nACGT\n>beta second sequence\nGGGG\nTTTT\n"
    parsed_fasta = list(SimpleFastaParser(StringIO(fasta_text)))
    assert parsed_fasta == [
        ("alpha first sequence", "ACGTACGT"),
        ("beta second sequence", "GGGGTTTT"),
    ]

    fastq_text = "@read1\nACGT\n+\nIIII\n@read2 comment\nTGCA\n+read2 comment\nJJJJ\n"
    parsed_fastq = list(FastqGeneralIterator(StringIO(fastq_text)))
    assert parsed_fastq[0] == ("read1", "ACGT", "IIII")
    assert parsed_fastq[1] == ("read2 comment", "TGCA", "JJJJ")


def check_alignio(tmp: Path) -> None:
    alignment = MultipleSeqAlignment(
        [
            SeqRecord(Seq("ACGT-ACGT"), id="alpha"),
            SeqRecord(Seq("AC-TTACGT"), id="beta"),
        ]
    )
    clustal = tmp / "alignment.aln"
    phylip = tmp / "alignment.phy"

    assert AlignIO.write([alignment], clustal, "clustal") == 1
    read_back = AlignIO.read(clustal, "clustal")
    assert len(read_back) == 2
    assert read_back.get_alignment_length() == 9

    assert AlignIO.convert(clustal, "clustal", phylip, "phylip") == 1
    converted = AlignIO.read(phylip, "phylip")
    assert len(converted) == 2
    assert converted.get_alignment_length() == 9

    fasta_blocks = StringIO(
        ">a1\nAAAA\n>b1\nAA-A\n>a2\nCCCC\n>b2\nCC-C\n"
    )
    blocks = list(AlignIO.parse(fasta_blocks, "fasta", seq_count=2))
    assert len(blocks) == 2
    assert all(len(block) == 2 for block in blocks)


def main() -> None:
    with TemporaryDirectory(prefix="biopython-file-io-") as tmpdir:
        tmp = Path(tmpdir)
        check_seqio(tmp)
        check_low_level_iterators()
        check_alignio(tmp)
    print("PASS seqio_alignio_smoke")


if __name__ == "__main__":
    main()
