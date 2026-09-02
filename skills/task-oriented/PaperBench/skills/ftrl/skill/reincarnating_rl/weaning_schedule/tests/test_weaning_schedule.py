import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "weaning_schedule.py"
spec = importlib.util.spec_from_file_location("weaning_schedule", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_linear_decay_is_monotone_and_clipped():
    values = [module.linear_decay(3.0, step, 10)["lambda_t"] for step in [0, 2, 5, 10, 12]]
    expected = [3.0, 2.4, 1.5, 0.0, 0.0]
    assert all(abs(value - target) < 1e-9 for value, target in zip(values, expected))


def test_performance_decay_weans_as_student_improves():
    low = module.performance_decay(2.0, 0.25, 1.0)
    high = module.performance_decay(2.0, 0.75, 1.0)
    done = module.performance_decay(2.0, 1.25, 1.0)
    assert low["lambda_t"] > high["lambda_t"]
    assert done["lambda_t"] == 0.0


def test_invalid_decay_steps_are_rejected():
    try:
        module.linear_decay(1.0, 0, 0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("invalid decay_steps was not rejected")


if __name__ == "__main__":
    test_linear_decay_is_monotone_and_clipped()
    test_performance_decay_weans_as_student_improves()
    test_invalid_decay_steps_are_rejected()


def test_negative_step_clips_to_initial_lambda():
    result = module.linear_decay(1.7, -5, 10)
    assert result["lambda_t"] == 1.7
    assert result["progress"] == 0.0
