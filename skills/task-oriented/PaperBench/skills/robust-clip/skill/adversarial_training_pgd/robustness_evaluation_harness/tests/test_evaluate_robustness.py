import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "linf_pgd_first_order_adversary", "scripts"))
from evaluate_robustness import LogisticModel, demo_data, evaluate


examples, labels = demo_data()
model = LogisticModel([1.2, 1.2], -1.2)
result = evaluate(model, examples, labels)
assert result["mechanism_checks"]["natural_metrics_computed"] is True
assert result["mechanism_checks"]["pgd_white_box_evaluation_executed"] is True
assert result["mechanism_checks"]["linf_projection_respected"] is True
assert isinstance(result["natural"]["accuracy"], float)
assert isinstance(result["pgd_adversarial"]["loss"], float)
assert result["pgd_adversarial"]["loss"] >= result["natural"]["loss"]
for diagnostic in result["attack_diagnostics"]:
    assert diagnostic["max_linf_perturbation"] <= 0.180000000001
