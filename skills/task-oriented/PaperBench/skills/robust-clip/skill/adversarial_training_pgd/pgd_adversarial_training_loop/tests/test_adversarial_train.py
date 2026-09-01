import os
import sys

base = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, base)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "linf_pgd_first_order_adversary", "scripts"))
from adversarial_train import LogisticModel, demo_data, train


examples, labels = demo_data()
model = LogisticModel([0.4, 0.4], -0.4)
result = train(model, examples, labels, epochs=8)
assert result["mechanism_checks"]["pgd_adversarial_examples_generated"] is True
assert result["mechanism_checks"]["optimizer_step_executed"] is True
assert result["params_before"] != result["params_after"]
assert result["loss_after"] < result["loss_before"]
assert len(result["training_trace"]) == 8
for epoch in result["training_trace"]:
    assert "params_before" in epoch and "params_after" in epoch
    assert epoch["params_before"] != epoch["params_after"]
    assert epoch["loss_after"] <= epoch["loss_before"] + 0.01
