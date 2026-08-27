#!/usr/bin/env python3
"""Safe offline smoke test for an installed Biopython package.

Run from any directory with the Python environment that should use Biopython:

    python scripts/biopython_quick_smoke.py

The check avoids network, databases, external executables, and original checkout
fixtures. It verifies representative imports and tiny in-memory workflows only.
"""

from __future__ import annotations

from io import StringIO

from Bio import Phylo, SeqIO, motifs
from Bio.Align import PairwiseAligner, substitution_matrices
from Bio.PDB import PDBParser
from Bio.Restriction import Analysis, EcoRI
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqUtils import gc_fraction


def main() -> None:
    seq = Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG")
    assert str(seq.translate(to_stop=True)) == "MAIVMGR"
    assert str(seq.reverse_complement())[:6] == "CTATCG"
    assert gc_fraction("ACGTACGT") == 0.5

    record = SeqRecord(seq, id="demo", description="demo sequence")
    fasta = record.format("fasta")
    parsed = SeqIO.read(StringIO(fasta), "fasta")
    assert parsed.id == "demo"
    assert len(parsed.seq) == len(seq)

    aligner = PairwiseAligner()
    aligner.mode = "local"
    assert aligner.score("ACCGT", "ACG") > 0
    matrix = substitution_matrices.load("BLOSUM62")
    assert matrix["A", "A"] > 0

    tree = Phylo.read(StringIO("(A:0.1,B:0.2);"), "newick")
    assert [terminal.name for terminal in tree.get_terminals()] == ["A", "B"]

    motif = motifs.create([Seq("ACGT"), Seq("ACGA")])
    assert motif.length == 4

    restriction = Analysis([EcoRI], Seq("GAATTC"), linear=True)
    assert restriction.full()[EcoRI] == [2]

    parser = PDBParser(QUIET=True)
    assert parser.__class__.__name__ == "PDBParser"

    print("PASS biopython_quick_smoke")


if __name__ == "__main__":
    main()
