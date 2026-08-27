#!/usr/bin/env python3
"""Offline smoke checks for Biopython specialized analysis modules.

This script uses only tiny in-memory data. It does not read original repository
files, contact network services, render graphics, require database credentials,
or invoke external bioinformatics executables.

Example:
    python scripts/specialized_modules_smoke.py
"""

from __future__ import annotations

import math


def check_motifs() -> None:
    from Bio import motifs
    from Bio.Seq import Seq

    motif = motifs.create([Seq("ATTA"), Seq("AATA"), Seq("ATCA")])
    assert len(motif) == 4
    assert str(motif.consensus) == "ATTA"
    assert motif.counts["A"] == [3.0, 1.0, 0.0, 3.0]

    motif.pseudocounts = 0.5
    pssm = motif.pssm
    same_length_score = float(pssm.calculate("ATTA"))
    assert math.isclose(same_length_score, float(pssm.max), rel_tol=1e-6)

    hits = list(pssm.search("GATTAG", threshold=float(pssm.max) - 1e-6, both=False))
    assert hits, "PSSM search should find the exact motif instance"
    assert int(hits[0][0]) == 1


def check_restriction() -> None:
    from Bio.Restriction import Analysis, EcoRI, RestrictionBatch
    from Bio.Seq import Seq

    seq = Seq("AAAAGAATTCTTTTGAATTC")
    cuts = EcoRI.search(seq)
    assert EcoRI.site == "GAATTC"
    assert cuts == [6, 16]

    analysis = Analysis(RestrictionBatch([EcoRI]), seq, linear=True)
    with_sites = analysis.with_sites()
    assert EcoRI in with_sites
    assert with_sites[EcoRI] == cuts

    fragments = [str(fragment) for fragment in EcoRI.catalyse(seq)]
    assert len(fragments) == 3
    assert fragments[1] == "AATTCTTTTG"


def check_protein_analysis() -> None:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis

    analysis = ProteinAnalysis("MAIVMGRWKGAR")
    counts = analysis.count_amino_acids()
    assert counts["M"] == 2
    assert counts["W"] == 1
    assert 1300.0 < analysis.molecular_weight() < 1500.0
    assert isinstance(analysis.gravy(), float)


def check_cluster() -> None:
    import numpy as np
    from Bio import Cluster

    data = np.array([[0.0, 0.0], [0.2, 0.1], [3.0, 3.1], [3.2, 2.9]])

    distances = Cluster.distancematrix(data, dist="e")
    assert len(distances) == 4
    assert len(distances[0]) == 0
    assert 0.0 < float(distances[1][0]) < 0.1

    tree = Cluster.treecluster(data, method="a", dist="e")
    assert len(tree) == 3
    tree_labels = [int(value) for value in tree.cut(2)]
    assert tree_labels[0] == tree_labels[1]
    assert tree_labels[2] == tree_labels[3]
    assert tree_labels[0] != tree_labels[2]

    labels, error, nfound = Cluster.kcluster(
        data, nclusters=2, initialid=[0, 0, 1, 1]
    )
    assert [int(value) for value in labels] == [0, 0, 1, 1]
    assert float(error) > 0.0
    assert int(nfound) >= 1


def main() -> None:
    check_motifs()
    check_restriction()
    check_protein_analysis()
    check_cluster()
    print("PASS specialized_modules_smoke")


if __name__ == "__main__":
    main()
