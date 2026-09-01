from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from contrastive_objective import compute_contrastive

images = [[1, 0], [0, 1]]
texts = [[0.99, 0.01], [0.01, 0.99]]
matched = compute_contrastive(images, texts, 10.0)
shuffled = compute_contrastive(images, list(reversed(texts)), 10.0)
assert matched["loss"] < shuffled["loss"]
assert matched["diagonal_margin_positive"] is True
assert all(abs(value - 1.0) < 1e-9 for value in matched["image_norms"])
try:
    compute_contrastive([[0, 0]], [[1, 0]], 1.0)
    raise AssertionError("expected zero-vector failure")
except ValueError:
    pass
