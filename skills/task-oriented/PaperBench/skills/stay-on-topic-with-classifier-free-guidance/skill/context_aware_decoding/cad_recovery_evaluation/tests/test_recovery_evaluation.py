from recovery_evaluation import evaluate_conflict_items, exact_match
def test_exact_match_normalizes_case_and_punctuation(): assert exact_match(" Alice! ", "alice")
def test_conflict_metrics_and_trace_checks():
    items=[{"id":"1","context_answer":"Alice","prior_answer":"Bob"}]
    traces={"1":{"prompt_separation_ok":True,"dual_logits_computed":True,"cad_adjustment_computed":True,"selection_trace":{"selected":"Alice"}}}
    out=evaluate_conflict_items(items,{"1":"Bob"},{"1":"Alice"},traces)
    assert out["metrics"]["regular_context_answer_exact_match"]==0.0
    assert out["metrics"]["cad_context_answer_exact_match"]==1.0
    assert out["mechanism_checks"]["cad_improves_over_regular"] is True
