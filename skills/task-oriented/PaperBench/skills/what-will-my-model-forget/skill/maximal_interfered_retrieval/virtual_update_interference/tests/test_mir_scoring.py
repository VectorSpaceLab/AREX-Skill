from mir_scoring import select_top_interfered, virtual_update


def test_virtual_update_does_not_mutate_params():
    params = {"weights": [0.0, 0.0], "bias": 0.0}
    incoming = [{"features": [1.0, 0.0], "label": 1}]
    updated = virtual_update(params, incoming, 0.5)
    assert params == {"weights": [0.0, 0.0], "bias": 0.0}
    assert updated["weights"][0] > 0.0


def test_harmed_candidate_ranks_first():
    params = {"weights": [0.0, 0.0], "bias": 0.0}
    incoming = [{"features": [1.0, 0.0], "label": 1}]
    candidates = [
        {"example_id": "harmed", "features": [1.0, 0.0], "label": 0},
        {"example_id": "helped", "features": [1.0, 0.0], "label": 1},
    ]
    result = select_top_interfered(params, incoming, candidates, 1.0, 1)
    assert result["selected"][0]["example_id"] == "harmed"
    assert result["selected"][0]["score"] > result["scores"][1]["score"]


def test_empty_candidates_and_smi2():
    params = {"weights": [0.0], "bias": 0.0}
    incoming = [{"features": [1.0], "label": 1}]
    assert select_top_interfered(params, incoming, [], 0.1, 2)["selected"] == []
    candidates = [{"example_id": "a", "features": [1.0], "label": 0, "best_loss": 0.1}]
    result = select_top_interfered(params, incoming, candidates, 1.0, 1, variant="smi_2")
    assert result["selected"][0]["score"] > 0.0
