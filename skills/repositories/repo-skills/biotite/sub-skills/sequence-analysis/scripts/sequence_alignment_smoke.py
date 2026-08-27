#!/usr/bin/env python3
"""Offline smoke checks for Biotite sequence and alignment APIs."""

from __future__ import annotations

import argparse
import sys


def check_core() -> None:
    import biotite.sequence as seq

    dna = seq.NucleotideSequence("ACGTNN", ambiguous=True)
    assert str(dna) == "ACGTNN", "ambiguous nucleotide construction changed"
    assert dna.reverse().complement().reverse().complement() == dna, (
        "reverse complement round trip failed"
    )

    strict = seq.NucleotideSequence("ACGT", ambiguous=False)
    assert str(strict) == "ACGT", "strict nucleotide construction failed"

    protein = seq.ProteinSequence("ACDE")
    assert str(protein) == "ACDE", "protein construction failed"
    assert seq.ProteinSequence.convert_letter_1to3("A") == "ALA", (
        "protein letter conversion failed"
    )

    coding = seq.NucleotideSequence("ATGGCGTAA")
    translated = coding.translate(complete=True)
    assert str(translated).startswith("MA"), "complete translation did not produce MA*"

    feature = seq.Feature("CDS", [seq.Location(1, 6)], qual={"gene": "toy"})
    annotated = seq.AnnotatedSequence(seq.Annotation([feature]), coding)
    extracted = annotated[feature]
    assert str(extracted) == "ATGGCG", "feature extraction changed"


def check_alignment() -> None:
    import biotite.sequence as seq
    import biotite.sequence.align as align

    seq1 = seq.ProteinSequence("BIQTITE")
    seq2 = seq.ProteinSequence("IQLITE")
    matrix = align.SubstitutionMatrix.std_protein_matrix()
    alignments = align.align_optimal(
        seq1,
        seq2,
        matrix,
        gap_penalty=-10,
        local=True,
        max_number=1,
    )
    assert len(alignments) == 1, "max_number=1 did not cap alignments"
    alignment = alignments[0]
    assert alignment.score == align.score(alignment, matrix, gap_penalty=-10), (
        "alignment score recalculation mismatch"
    )
    assert align.get_sequence_identity(alignment) > 0, "sequence identity is not positive"

    nucleotide_matrix = align.SubstitutionMatrix.std_nucleotide_matrix()
    nuc_alignment = align.align_optimal(
        seq.NucleotideSequence("ACCTGA"),
        seq.NucleotideSequence("ACTGGT"),
        nucleotide_matrix,
        gap_penalty=-7,
        max_number=1,
    )[0]
    assert nuc_alignment.score == align.score(
        nuc_alignment,
        nucleotide_matrix,
        gap_penalty=-7,
    ), "nucleotide alignment score mismatch"

    reference = seq.ProteinSequence("GIPCGESCVFIPCISSVVGCSCKSKVCYLD")
    query = seq.ProteinSequence("GIPCAESCVWIPCTVTALLGCSCKDKVCYLD")
    table = align.KmerTable.from_sequences(k=3, sequences=[reference], ref_ids=[0])
    matches = table.match(query)
    assert matches.shape[1] == 3, "k-mer match rows should contain query/ref/position"
    assert len(matches) > 0, "expected at least one k-mer match"


def check_profile() -> None:
    import numpy as np
    import biotite.sequence as seq
    import biotite.sequence.align as align
    import biotite.sequence.phylo as phylo

    alignment = align.Alignment.from_strings(
        ["CGTCAT--", "--TCATGC"],
        seq.NucleotideSequence,
    )
    profile = seq.SequenceProfile.from_alignment(alignment)
    assert str(profile.to_consensus()) == "CGTCATGC", "profile consensus changed"
    assert profile.symbols.shape[0] == len(alignment), "profile/alignment length mismatch"
    assert profile.gaps.shape[0] == len(alignment), "profile gap length mismatch"
    assert profile.sequence_score(seq.NucleotideSequence("CGTCATGC"), pseudocount=1) > 0, (
        "profile sequence score should be positive for consensus"
    )

    distances = np.array(
        [
            [0.0, 1.0, 4.0],
            [1.0, 0.0, 4.0],
            [4.0, 4.0, 0.0],
        ]
    )
    tree = phylo.upgma(distances)
    newick = tree.to_newick(labels=["A", "B", "C"], include_distance=False)
    assert "A" in newick and "B" in newick and "C" in newick, (
        "UPGMA Newick output missing labels"
    )


CHECKS = {
    "core": check_core,
    "alignment": check_alignment,
    "profile": check_profile,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run offline Biotite sequence/alignment smoke checks."
    )
    parser.add_argument(
        "--mode",
        choices=["all", *CHECKS],
        default="all",
        help="Subset to run. Default: all.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    names = list(CHECKS) if args.mode == "all" else [args.mode]
    for name in names:
        try:
            CHECKS[name]()
        except Exception as error:
            print(f"[FAIL] {name}: {error}", file=sys.stderr)
            return 1
        else:
            print(f"[OK] {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
