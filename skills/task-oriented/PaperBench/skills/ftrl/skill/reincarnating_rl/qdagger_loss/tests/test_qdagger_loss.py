import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "qdagger_loss.py"
spec = importlib.util.spec_from_file_location("qdagger_loss", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_qdagger_loss_components_are_reported():
    q_values = {"0": [0.0, 1.0], "1": [1.0, 0.0]}
    transitions = [
        {"state": "0", "action": 1, "n_step_return": 1.0, "discount": 0.5, "next_max_q": 1.0, "teacher_policy": [0.1, 0.9]},
        {"state": "1", "action": 0, "n_step_return": 0.5, "discount": 0.0, "next_max_q": 0.0, "teacher_policy": [0.8, 0.2]},
    ]
    result = module.compute_qdagger_loss(q_values, transitions, temperature=0.5, lambda_t=2.0)
    assert result["td_loss"] > 0
    assert result["distillation_loss"] > 0
    assert result["combined_loss"] == result["td_loss"] + 2.0 * result["distillation_loss"]
    assert len(result["examples"]) == 2


def test_teacher_aligned_q_values_reduce_distillation():
    transitions = [{"state": "s", "action": 1, "n_step_return": 0.0, "discount": 0.0, "next_max_q": 0.0, "teacher_policy": [0.0, 1.0]}]
    aligned = module.compute_qdagger_loss({"s": [0.0, 2.0]}, transitions, temperature=1.0, lambda_t=1.0)
    misaligned = module.compute_qdagger_loss({"s": [2.0, 0.0]}, transitions, temperature=1.0, lambda_t=1.0)
    assert aligned["distillation_loss"] < misaligned["distillation_loss"]


def test_invalid_teacher_policy_is_rejected():
    transitions = [{"state": "s", "action": 0, "n_step_return": 0.0, "discount": 0.0, "next_max_q": 0.0, "teacher_policy": [0.4, 0.4]}]
    try:
        module.compute_qdagger_loss({"s": [0.0, 1.0]}, transitions)
    except ValueError as exc:
        assert "sum to 1" in str(exc)
    else:
        raise AssertionError("invalid teacher policy was not rejected")


if __name__ == "__main__":
    test_qdagger_loss_components_are_reported()
    test_teacher_aligned_q_values_reduce_distillation()
    test_invalid_teacher_policy_is_rejected()


def test_lambda_zero_removes_distillation_from_combined_loss():
    transitions = [{"state": "s", "action": 0, "n_step_return": 1.0, "discount": 0.0, "next_max_q": 0.0, "teacher_policy": [1.0, 0.0]}]
    result = module.compute_qdagger_loss({"s": [0.2, 0.0]}, transitions, temperature=1.0, lambda_t=0.0)
    assert result["combined_loss"] == result["td_loss"]
