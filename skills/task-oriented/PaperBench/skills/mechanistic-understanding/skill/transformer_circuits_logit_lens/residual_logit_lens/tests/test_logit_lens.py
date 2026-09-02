from logit_lens import analyze


def test_component_logits_sum_to_full_logits():
    a = [[1, 0], [0, 1]]
    b = [[0, 2], [3, 0]]
    residual = [[1, 2], [3, 1]]
    unembedding = [[1, 0, 2], [0, 1, -1]]
    result = analyze(residual, unembedding, {'a': a, 'b': b})
    assert result['logits'] == [[1, 2, 0], [3, 1, 5]]
    assert result['max_reconstruction_error'] == 0
