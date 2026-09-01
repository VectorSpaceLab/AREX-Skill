from protocol_check import validate_protocol


def test_target_only_protocol_passes():
    metadata = {"adaptation_inputs": ["target_inputs", "target_batch_statistics"], "loss_inputs": ["entropy_loss"], "evaluation_inputs": ["target_labels"]}
    assert validate_protocol(metadata)["ok"] is True


def test_label_leakage_fails():
    metadata = {"adaptation_inputs": ["target_inputs"], "loss_inputs": ["target_labels"]}
    report = validate_protocol(metadata)
    assert report["ok"] is False
    assert "target_labels" in report["violations"]
