import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pbt_self_play.py"
spec = importlib.util.spec_from_file_location("pbt_self_play", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_policy_assignment_is_deterministic_with_seed():
    first = module.assign_policies(["a", "b", "c"], ["p0", "p1"], seed=7)
    second = module.assign_policies(["a", "b", "c"], ["p0", "p1"], seed=7)
    assert first == second
    assert len(first) == 3


def test_pbt_replaces_weak_policy():
    scores = {"p0": 1.0, "p1": 0.4, "p2": 0.8}
    hyper = {policy: {"learning_rate": 0.001} for policy in scores}
    result = module.pbt_decisions(scores, hyper, threshold_fraction=0.5, mutation_factor=2.0, bounds={"learning_rate": (1e-5, 0.01)})
    weak = [decision for decision in result["decisions"] if decision["policy_id"] == "p1"][0]
    assert weak["action"] == "replace_and_mutate"
    assert weak["source_policy_id"] == "p0"
    assert weak["new_hyperparameters"]["learning_rate"] == 0.002


def test_all_zero_scores_do_not_replace_arbitrarily():
    scores = {"p0": 0.0, "p1": 0.0}
    hyper = {policy: {"learning_rate": 0.001} for policy in scores}
    result = module.pbt_decisions(scores, hyper)
    assert all(decision["action"] == "keep" for decision in result["decisions"])


def test_mutation_bounds_are_applied():
    mutated = module.mutate_hyperparameters({"learning_rate": 0.009}, factor=2.0, bounds={"learning_rate": (1e-5, 0.01)})
    assert mutated["learning_rate"] == 0.01
