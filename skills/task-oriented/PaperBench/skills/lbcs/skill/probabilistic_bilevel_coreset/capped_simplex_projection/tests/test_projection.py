from projection import project_capped_simplex


def test_feasible_vector_is_preserved_after_clipping():
    out = project_capped_simplex([0.2, 0.3, -1.0], 1.0)
    assert out == [0.2, 0.3, 0.0]


def test_active_budget_projection():
    out = project_capped_simplex([0.9, 0.8, 0.7], 1.0)
    assert all(0.0 <= value <= 1.0 for value in out)
    assert abs(sum(out) - 1.0) < 1e-6


def test_zero_and_full_budget():
    assert project_capped_simplex([0.5, 0.5], 0.0) == [0.0, 0.0]
    assert project_capped_simplex([2.0, -1.0], 3.0) == [1.0, 0.0]
