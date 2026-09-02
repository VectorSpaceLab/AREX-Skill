def check_trace(trace):
    required = ["params_before", "params_after", "loss_before", "loss_after", "relative_l2_before", "relative_l2_after", "lambda_history"]
    missing = [key for key in required if key not in trace]
    if missing:
        raise AssertionError("missing trace keys: " + ", ".join(missing))
    if trace["params_before"] == trace["params_after"]:
        raise AssertionError("parameters did not change")
    if not trace["lambda_history"]:
        raise AssertionError("lambda history is empty")
    return True
