from proxy_utils import accuracy, mechanism_summary


def test_accuracy_and_summary():
    assert accuracy(["a", "b"], ["a", "b"]) == 1.0
    checks = {"pair_protocol_validated": True, "contrastive_loss_computed": True, "optimizer_step_executed": True, "prompt_zeroshot_executed": True, "source_boundary_respected": True}
    assert mechanism_summary(checks)["all_required_passed"] is True
