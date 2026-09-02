import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "perturbation_metrics.py"
spec = importlib.util.spec_from_file_location("perturbation_metrics", SCRIPT)
perturbation_metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(perturbation_metrics)


def test_sequence_flip_stats():
    stats = perturbation_metrics.sequence_flip_stats([1, 1, 2, 2, 3])
    assert stats["flips"] == 2
    assert stats["transitions"] == 4
    assert abs(stats["flip_probability"] - 0.5) < 1e-9


def test_grouped_mean_flip_probability():
    result = perturbation_metrics.compute_flip_probabilities({"translate": [[1, 1, 2]], "tilt": [[3, 3, 3]]})
    assert abs(result["flip_probability_by_group"]["translate"]["flip_probability"] - 0.5) < 1e-9
    assert result["flip_probability_by_group"]["tilt"]["flip_probability"] == 0.0
    assert abs(result["mean_flip_probability"] - 0.25) < 1e-9


def test_rejects_length_one_sequence():
    try:
        perturbation_metrics.compute_flip_probabilities({"translate": [[1]]})
    except ValueError as exc:
        assert "at least two" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_sequence_flip_stats()
    test_grouped_mean_flip_probability()
    test_rejects_length_one_sequence()
