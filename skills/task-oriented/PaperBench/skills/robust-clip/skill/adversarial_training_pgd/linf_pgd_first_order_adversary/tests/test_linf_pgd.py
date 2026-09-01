import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from linf_pgd import LogisticModel, demo_data, linf_distance, pgd_attack


model = LogisticModel([3.0, 3.0], -3.0)
examples, labels = demo_data()
result = pgd_attack(model, examples, labels, epsilon=0.2, step_size=0.1, steps=4, restarts=2, seed=7)

assert len(result["adversarial_examples"]) == len(examples)
for original, adversarial, diagnostic, trajectory in zip(examples, result["adversarial_examples"], result["diagnostics"], result["trajectories"]):
    assert linf_distance(original, adversarial) <= 0.200000000001
    assert diagnostic["within_epsilon"] is True
    assert trajectory["best_loss"] >= trajectory["natural_loss"]

large_step = pgd_attack(model, examples, labels, epsilon=0.2, step_size=2.0, steps=2, restarts=1, seed=3)
for original, adversarial, diagnostic in zip(examples, large_step["adversarial_examples"], large_step["diagnostics"]):
    assert linf_distance(original, adversarial) <= 0.200000000001
    assert diagnostic["within_clip"] is True

multi_restart = pgd_attack(model, examples, labels, epsilon=0.2, step_size=0.07, steps=3, restarts=4, seed=13)
for trajectory in multi_restart["trajectories"]:
    restart_losses = [restart["final_loss"] for restart in trajectory["restarts"]]
    assert abs(trajectory["best_loss"] - max([trajectory["natural_loss"]] + restart_losses)) < 1e-12
