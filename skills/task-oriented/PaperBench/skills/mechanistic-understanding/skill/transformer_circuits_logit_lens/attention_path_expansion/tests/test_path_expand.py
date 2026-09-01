from path_expand import analyze


def test_virtual_path_matches_explicit_frozen_forward():
    eye2 = [[1,0],[0,1]]
    data = {
        'tokens': [0,1],
        'embedding': eye2,
        'unembedding': eye2,
        'attention_patterns': [eye2, eye2],
        'ov_matrices': [eye2, eye2],
    }
    out = analyze(data)
    assert out['max_consistency_error'] == 0
    assert out['virtual_logits'] == eye2
