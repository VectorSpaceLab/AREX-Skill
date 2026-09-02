from circuit_expand import summarize_copying


def test_off_diagonal_matrix_is_not_copying_dominant():
    summary = summarize_copying([[0, 3], [3, 0]])
    assert summary['diagonal_dominance'] < 0
