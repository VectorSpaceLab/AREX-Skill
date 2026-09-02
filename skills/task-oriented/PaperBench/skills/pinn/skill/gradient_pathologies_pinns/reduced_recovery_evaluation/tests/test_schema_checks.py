from schema_checks import check_trace

def test_trace_schema_accepts_optimizer_evidence():
    trace = {"params_before":[0.0],"params_after":[1.0],"loss_before":2.0,"loss_after":1.0,"relative_l2_before":1.0,"relative_l2_after":0.5,"lambda_history":[1.2]}
    assert check_trace(trace)
