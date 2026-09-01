from nce_train import default_features, demo_payload, energy, train_nce


def test_nce_training_decreases_loss_and_changes_params():
    result = train_nce(demo_payload(), steps=60, lr=0.8)
    assert result["loss_after"] < result["loss_before"]
    assert result["params_after"] != result["params_before"]
    assert result["optimizer_state_changed"] is True


def test_positive_energy_is_lower_than_negative_energy():
    result = train_nce(demo_payload(), steps=80, lr=0.8)
    assert result["positive_energy_after"] < result["negative_energy_after"]
    assert result["energy_gap_after"] > 0.0


def test_adversarial_repeated_quality_terms_remain_high_energy():
    payload = demo_payload()
    payload["negatives"].append(
        {"id": "adversarial", "text": "clear clear evidence policy policy policy development"}
    )
    result = train_nce(payload, steps=110, lr=0.7)
    params = result["params_after"]
    positive_energy = energy(params, default_features(payload["positives"][0]["text"]))
    adversarial_energy = energy(params, default_features(payload["negatives"][-1]["text"]))
    assert positive_energy < adversarial_energy
