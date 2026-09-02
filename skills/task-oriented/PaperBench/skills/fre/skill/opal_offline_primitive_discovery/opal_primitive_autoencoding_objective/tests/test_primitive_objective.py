from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from primitive_objective import train_reduced_objective


def test_reconstruction_loss_decreases_and_latents_separate():
    payload = {"segments": [
        {"actions": [-1, -1, -1], "initial_state": -1},
        {"actions": [1, 1, 1], "initial_state": 1},
    ]}
    result = train_reduced_objective(payload, steps=4)
    assert result["optimizer_step_executed"] is True
    assert result["reconstruction_loss_after"] < result["reconstruction_loss_before"]
    assert result["latent_separation"] > 0.5
    assert "prior_penalty_after" in result


def test_prior_penalty_detects_initial_state_mismatch():
    payload = {"segments": [{"actions": [1, 1], "initial_state": -1}]}
    result = train_reduced_objective(payload, steps=1)
    assert result["prior_penalty_after"] == 1.0


if __name__ == "__main__":
    test_reconstruction_loss_decreases_and_latents_separate()
    test_prior_penalty_detects_initial_state_mismatch()
