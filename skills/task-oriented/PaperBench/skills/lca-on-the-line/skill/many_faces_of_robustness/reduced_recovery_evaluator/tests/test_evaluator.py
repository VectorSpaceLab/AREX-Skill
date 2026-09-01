from evaluator import build_result, trace_has_update

def test_build_result_requires_mechanism_checks():
    target={"dataset":"proxy","proxy":True}
    try:
        build_result("paper", target, {"metric":1.0}, ["cmd"], {}, 2)
    except ValueError as exc:
        assert "mechanism" in str(exc)
    else:
        raise AssertionError("expected missing mechanism rejection")

def test_trace_update():
    assert trace_has_update({"loss_before":1.0,"loss_after":0.5,"params_before":[0],"params_after":[1]})
