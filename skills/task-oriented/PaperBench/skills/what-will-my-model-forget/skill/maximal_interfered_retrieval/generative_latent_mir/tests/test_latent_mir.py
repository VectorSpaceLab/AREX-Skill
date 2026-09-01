from latent_mir import kl_divergence, select_diverse_latents


def test_kl_handles_smoothing_and_ranking():
    assert kl_divergence([1.0, 0.0], [0.5, 0.5]) > 0.0
    candidates = [
        {"candidate_id": "low", "latent": [0.0, 0.0], "pre_probs": [0.9, 0.1], "virtual_probs": [0.8, 0.2]},
        {"candidate_id": "high", "latent": [2.0, 0.0], "pre_probs": [0.9, 0.1], "virtual_probs": [0.2, 0.8]},
    ]
    result = select_diverse_latents(candidates, budget=1)
    assert result["selected"][0]["candidate_id"] == "high"


def test_entropy_penalty_and_diversity_filter():
    candidates = [
        {"candidate_id": "uncertain", "latent": [0.0, 0.0], "pre_probs": [0.5, 0.5], "virtual_probs": [0.9, 0.1]},
        {"candidate_id": "confident", "latent": [0.1, 0.0], "pre_probs": [0.99, 0.01], "virtual_probs": [0.8, 0.2]},
        {"candidate_id": "far", "latent": [5.0, 0.0], "pre_probs": [0.99, 0.01], "virtual_probs": [0.8, 0.2]},
    ]
    result = select_diverse_latents(candidates, budget=3, entropy_weight=0.5, min_distance=1.0)
    ids = [item["candidate_id"] for item in result["selected"]]
    assert "uncertain" in ids
    assert "far" in ids
    assert "confident" not in ids
    assert len(ids) == 2
    assert result["mechanism_checks"]["diversity_filter_evaluated"] is True
