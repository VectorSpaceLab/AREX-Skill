def build_result(paper_id, target, metrics, commands, mechanism_checks, sample_count):
    if not any(isinstance(v,(int,float)) for v in metrics.values()):
        raise ValueError("at least one numeric metric is required")
    if target.get("proxy") and not mechanism_checks:
        raise ValueError("proxy recovery requires mechanism checks")
    return {"schema_version":1,"paper_id":paper_id,"experiment":target["dataset"],"is_proxy":bool(target.get("proxy")),"sample_count":sample_count,"metrics":metrics,"paper_target":target,"commands":commands,"artifacts":["recovery/logs/training_trace.json"],"mechanism_checks":mechanism_checks,"notes":"Declared reduced proxy recovery."}

def trace_has_update(trace):
    return trace.get("loss_after", 1e9) < trace.get("loss_before", -1e9) and trace.get("params_before") != trace.get("params_after")
