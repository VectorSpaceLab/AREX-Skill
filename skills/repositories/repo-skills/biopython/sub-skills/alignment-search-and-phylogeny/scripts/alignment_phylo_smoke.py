#!/usr/bin/env python3
"""Offline smoke checks for Biopython alignment, SearchIO, and Phylo APIs."""

from __future__ import annotations

import copy
import math
from io import StringIO


def check_pairwise_aligner() -> None:
    from Bio import Align

    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 2.0
    aligner.mismatch_score = -1.0
    aligner.open_gap_score = -2.0
    aligner.extend_gap_score = -0.5

    score = aligner.score("GATTACA", "GCATGCU")
    assert math.isclose(score, 2.0), score

    alignments = aligner.align("GATTACA", "GCATGCU")
    first = alignments[0]
    assert math.isclose(first.score, score), first.score
    assert len(first.target) == 7
    assert len(first.query) == 7


def check_substitution_matrices() -> None:
    from Bio import Align
    from Bio.Align import substitution_matrices

    names = substitution_matrices.load()
    assert "BLOSUM62" in names

    matrix = substitution_matrices.load("BLOSUM62")
    assert matrix.alphabet.startswith("ARNDC"), matrix.alphabet
    assert math.isclose(matrix["A", "A"], 4.0)
    assert math.isclose(matrix["W", "W"], 11.0)
    assert math.isclose(matrix["A", "R"], -1.0)

    aligner = Align.PairwiseAligner()
    aligner.substitution_matrix = matrix
    aligner.open_gap_score = -10.0
    aligner.extend_gap_score = -0.5
    assert math.isclose(aligner.score("MEEPQ", "MEEPQ"), 27.0)


def check_searchio_model_available() -> None:
    from Bio import SearchIO
    from Bio.SearchIO._model import HSP
    from Bio.SearchIO._model import HSPFragment
    from Bio.SearchIO._model import Hit
    from Bio.SearchIO._model import QueryResult

    fragment = HSPFragment(hit_id="hit1", query_id="query1")
    hsp = HSP([fragment])
    hit = Hit([hsp], id="hit1", query_id="query1")
    qresult = QueryResult([hit], id="query1")

    assert SearchIO.__name__ == "Bio.SearchIO"
    assert qresult.id == "query1"
    assert len(qresult) == 1
    assert qresult.hit_keys == ["hit1"]
    assert qresult[0].id == "hit1"
    assert qresult["hit1"].query_id == "query1"


def check_phylo_newick_traversal_and_edit() -> None:
    from Bio import Phylo

    newick = "((Alpha:0.1,Beta:0.2)Inner:0.3,Gamma:0.4)Root;"
    tree = Phylo.read(StringIO(newick), "newick")

    assert tree.root.name == "Root"
    assert tree.count_terminals() == 3
    assert [clade.name for clade in tree.find_clades(terminal=True)] == [
        "Alpha",
        "Beta",
        "Gamma",
    ]

    inner = tree.common_ancestor("Alpha", "Beta")
    assert inner.name == "Inner"
    assert math.isclose(tree.distance("Alpha", "Beta"), 0.3)

    working = copy.deepcopy(tree)
    working.ladderize()
    parent = working.prune("Gamma")
    assert parent.name == "Inner"
    assert working.count_terminals() == 2
    assert {clade.name for clade in working.get_terminals()} == {"Alpha", "Beta"}

    out = StringIO()
    assert Phylo.write(working, out, "newick") == 1
    assert "Alpha" in out.getvalue() and "Beta" in out.getvalue()


def main() -> int:
    check_pairwise_aligner()
    check_substitution_matrices()
    check_searchio_model_available()
    check_phylo_newick_traversal_and_edit()
    print("PASS alignment_phylo_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
