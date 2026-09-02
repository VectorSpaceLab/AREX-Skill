from transition_batch import build_transition_skill_batch, deterministic_synthetic_batch


def test_concat_and_metadata():
    batch = build_transition_skill_batch([[1, 2]], [[3, 4]], [[0.5, 0.2]])
    assert batch["tau"] == [[1.0, 2.0, 3.0, 4.0]]
    assert batch["metadata"]["transition_dim"] == 4


def test_synthetic_batch_is_deterministic():
    first = deterministic_synthetic_batch(seed=3)
    second = deterministic_synthetic_batch(seed=3)
    assert first == second
    assert first["metadata"]["batch_size"] == 8


def test_rejects_misaligned_skills():
    try:
        build_transition_skill_batch([[1]], [[2]], [[0], [1]])
    except ValueError as exc:
        assert "same batch size" in str(exc)
    else:
        raise AssertionError("expected ValueError")
