from losses import compute_losses

class TinyModel:
    weights = [0.1]
    def predict(self, x, y):
        return self.weights[0] * x * y

def test_losses_remain_separate_and_weighted():
    problem = {"interior": [(0.2, 0.3)], "boundary": [(1.0, 0.2)], "boundary_values": [0.0]}
    out = compute_losses(TinyModel(), problem, lambda x, y: 1.0, [3.0])
    assert out["residual_loss"] >= 0.0
    assert out["boundary_loss"] >= 0.0
    assert out["total_loss"] == out["residual_loss"] + 3.0 * out["boundary_loss"]
