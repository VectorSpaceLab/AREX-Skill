from lexiflow_direct_search import first_objective_baseline, run_lexiflow, synthetic_objective


def test_direct_search_runs_and_records_acceptance():
    result = run_lexiflow(synthetic_objective, [[0.0, 1.0]], [None, None], [0.03, 0.0], seed=7, budget=60)
    assert len(result["history"]) == 60
    assert any(item["accepted"] for item in result["trace"])
    assert result["best_objectives"][0] <= result["targets"][0]


def test_baseline_optimizes_first_objective_only():
    result = first_objective_baseline(seed=7, budget=20)
    assert len(result["history"]) == 20
    assert result["best_objectives"][0] == min(item["objectives"][0] for item in result["history"])
