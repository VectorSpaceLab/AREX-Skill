def accuracy(predictions, labels):
    if len(predictions) != len(labels) or not labels:
        raise ValueError("predictions and labels must have same non-zero length")
    return sum(p == y for p, y in zip(predictions, labels)) / len(labels)


def mechanism_summary(checks):
    required = ["pair_protocol_validated", "contrastive_loss_computed", "optimizer_step_executed", "prompt_zeroshot_executed", "source_boundary_respected"]
    return {"all_required_passed": all(checks.get(k) is True for k in required), "required": required}
