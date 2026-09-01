import re
def normalize(text): return re.sub(r"[^a-z0-9 ]+", "", str(text).lower()).strip()
def exact_match(pred, gold): return normalize(pred)==normalize(gold)
def evaluate_conflict_items(items, regular_predictions, cad_predictions, traces):
    records=[]; reg_ok=0; cad_ok=0; trace_ok=True
    for item in items:
        iid=item["id"]; gold=item["context_answer"]; rp=regular_predictions[iid]; cp=cad_predictions[iid]
        r_ok=exact_match(rp,gold); c_ok=exact_match(cp,gold); reg_ok+=int(r_ok); cad_ok+=int(c_ok)
        tr=traces.get(iid,{}); required=["prompt_separation_ok","dual_logits_computed","cad_adjustment_computed","selection_trace"]
        item_trace_ok=all(bool(tr.get(k)) for k in required); trace_ok=trace_ok and item_trace_ok
        records.append({"id":iid,"context_answer":gold,"prior_answer":item.get("prior_answer"),"regular_prediction":rp,"cad_prediction":cp,"regular_em":r_ok,"cad_em":c_ok,"trace_ok":item_trace_ok})
    n=len(items); metrics={"regular_context_answer_exact_match":reg_ok/n if n else 0.0,"cad_context_answer_exact_match":cad_ok/n if n else 0.0,"cad_improvement":(cad_ok-reg_ok)/n if n else 0.0}
    checks={"prompt_separation_executed":trace_ok,"dual_forward_logits_available":trace_ok,"cad_logit_adjustment_executed":trace_ok,"context_answer_metric_computed":True,"cad_improves_over_regular":metrics["cad_improvement"]>0}
    return {"metrics":metrics,"records":records,"mechanism_checks":checks}
