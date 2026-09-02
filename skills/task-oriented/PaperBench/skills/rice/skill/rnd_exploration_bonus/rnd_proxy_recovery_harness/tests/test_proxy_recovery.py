from run_proxy_recovery import synthetic_vectors


def test_synthetic_vectors_have_seen_target_and_heldout_sets():
    data = synthetic_vectors(3)
    assert len(data["seen"]) > len(data["target_train"])
    assert len(data["heldout_target"]) == 3
    assert data["seen"][0][0] > data["seen"][0][1]
    assert data["target_train"][0][1] > data["target_train"][0][0]
