import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from proxy_softmax import cross_entropy_loss, gradient_step, initial_weights, make_proxy_dataset, predict_probabilities


def test_probabilities_sum_to_one():
    data = make_proxy_dataset()
    probabilities = predict_probabilities(data["features"], initial_weights())
    assert len(probabilities) == len(data["labels"])
    for row in probabilities:
        assert abs(sum(row) - 1.0) < 1e-9


def test_gradient_step_changes_params_and_loss():
    data = make_proxy_dataset()
    before = initial_weights()
    loss_before = cross_entropy_loss(data["features"], data["labels"], before)
    after = gradient_step(data["features"], data["labels"], before, learning_rate=0.4)
    loss_after = cross_entropy_loss(data["features"], data["labels"], after)
    assert after != before
    assert loss_after < loss_before


if __name__ == "__main__":
    test_probabilities_sum_to_one()
    test_gradient_step_changes_params_and_loss()
    print("ok")
