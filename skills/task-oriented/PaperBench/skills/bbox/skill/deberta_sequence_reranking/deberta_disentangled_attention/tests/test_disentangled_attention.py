from disentangled_attention import compute_attention, relative_index_matrix


def test_relative_index_matrix_clips_distances():
    matrix = relative_index_matrix(4, 2)
    assert matrix == [
        [2, 1, 0, 0],
        [3, 2, 1, 0],
        [3, 3, 2, 1],
        [3, 3, 3, 2],
    ]


def test_c2p_and_p2c_are_distinct_on_asymmetric_tokens():
    result = compute_attention(["deep", "learning", "works"], max_relative_distance=2)
    c2p = result["components"]["c2p"]
    p2c = result["components"]["p2c"]
    assert c2p[0][1] != p2c[0][1]
    assert result["combined"][0][1] != result["components"]["c2c"][0][1]


def test_ablation_changes_combined_scores():
    full = compute_attention(["deep", "learning", "works"], active_terms=["c2c", "c2p", "p2c"])
    no_p2c = compute_attention(["deep", "learning", "works"], active_terms=["c2c", "c2p"])
    assert full["combined"] != no_p2c["combined"]
