from graph_attention import build_attention_mask, build_bcmf_attention, unpack_mask


def test_bcmf_mask_has_expected_edges_and_sparse_roundtrip():
    result = build_bcmf_attention(2, 2, 2)
    nodes = result["nodes"]
    mask = result["mask"]
    index = {node: pos for pos, node in enumerate(nodes)}
    assert result["stats"]["node_count"] == 20
    assert mask[index["A[0,0]"]][index["C[0,0,1]"]]
    assert mask[index["R[0,1]"]][index["C[0,0,1]"]]
    assert mask[index["C[0,0,1]"]][index["E[0,1]"]]
    assert not mask[index["A[0,0]"]][index["R[0,1]"]]
    assert unpack_mask(result["packed"], len(nodes)) == mask


def test_factor_scope_adds_clique_edges():
    nodes = ["x0", "x1", "x2"]
    mask = build_attention_mask(nodes, [], [["x0", "x1", "x2"]])
    assert all(mask[i][j] for i in range(3) for j in range(3))


def test_bcmf_mask_remains_sparse_when_dimensions_grow():
    result = build_bcmf_attention(3, 2, 2)
    node_count = result["stats"]["node_count"]
    assert result["stats"]["max_attendable"] == 4
    assert result["stats"]["allowed_pairs"] < node_count * node_count / 5
    assert unpack_mask(result["packed"], node_count) == result["mask"]
