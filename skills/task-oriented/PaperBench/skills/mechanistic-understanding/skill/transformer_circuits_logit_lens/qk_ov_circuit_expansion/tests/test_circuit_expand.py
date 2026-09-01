from circuit_expand import analyze, summarize_copying


def test_identity_expansion_and_copying_summary():
    data = {
        'embedding': [[1,0],[0,1]],
        'unembedding': [[1,0],[0,1]],
        'w_qk': [[2,0],[0,3]],
        'w_ov': [[4,0],[0,5]],
    }
    out = analyze(data)
    assert out['expanded_qk'] == [[2,0],[0,3]]
    assert out['expanded_ov'] == [[4,0],[0,5]]
    assert out['ov_copying_summary']['diagonal_dominance'] > 0
    assert out['ov_copying_summary']['positive_real_eigen_fraction'] == 1.0
