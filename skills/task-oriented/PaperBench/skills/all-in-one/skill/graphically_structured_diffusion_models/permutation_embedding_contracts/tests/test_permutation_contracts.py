import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "graph_structure_attention" / "scripts"))

from graph_attention import build_bcmf_attention
from permutation_contracts import (
    bcmf_swap_i_permutation,
    embedding_groups,
    partial_swap_permutation,
    preserves_mask,
)


def test_full_bcmf_i_plate_swap_preserves_mask():
    graph = build_bcmf_attention(2, 2, 2)
    perm = bcmf_swap_i_permutation(graph["nodes"], 0, 1)
    assert preserves_mask(graph["mask"], perm)["preserves_mask"] is True


def test_partial_swap_does_not_preserve_structured_mask():
    graph = build_bcmf_attention(2, 2, 2)
    perm = partial_swap_permutation(graph["nodes"], "A[0,0]", "A[1,0]")
    check = preserves_mask(graph["mask"], perm)
    assert check["preserves_mask"] is False
    assert check["mismatch"] is not None


def test_rectangular_bcmf_keeps_full_plate_and_partial_swap_distinct():
    graph = build_bcmf_attention(2, 3, 2)
    full = preserves_mask(graph["mask"], bcmf_swap_i_permutation(graph["nodes"], 0, 1))
    partial = preserves_mask(graph["mask"], partial_swap_permutation(graph["nodes"], "A[0,0]", "A[1,0]"))
    assert full["preserves_mask"] is True
    assert partial["preserves_mask"] is False


def test_embedding_groups_modes_are_distinct():
    nodes = ["A[0,0]", "A[0,1]", "R[0,0]"]
    independent = embedding_groups(nodes, "independent")
    array = embedding_groups(nodes, "array")
    assert len(set(independent.values())) == 3
    assert array["A[0,0]"] == array["A[0,1]"]
    assert array["A[0,0]"] != array["R[0,0]"]
