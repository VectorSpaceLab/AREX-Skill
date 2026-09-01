import argparse, json

def normalize(value): return str(value or "").strip().lower()
def accuracy(labels,preds): return 0.0 if not labels else sum(1 for l,p in zip(labels,preds) if normalize(l)==normalize(p))/len(labels)
def evaluate(heldout, before_predictions, after_predictions, mixture_audit, training_trace, target):
    labels=[item.get("answer") for item in heldout]; before=accuracy(labels,before_predictions); after=accuracy(labels,after_predictions)
    loss_before=float(training_trace.get("loss_before", 0.0)); loss_after=float(training_trace.get("loss_after", loss_before)); loss_delta=loss_before-loss_after
    retained={normalize(x) for x in mixture_audit.get("retained_task_ids",[])}; heldout_ids={normalize(x.get("task_id")) for x in heldout}
    cot=[x for x in heldout if x.get("format_mode") == "cot" or x.get("metadata",{}).get("cot_used")]
    checks={"heldout_exclusion_passed": not bool(retained & heldout_ids), "cot_coverage_present": bool(cot), "optimizer_step_executed": bool(training_trace.get("optimizer_step_executed")), "reduced_training_executed": bool(training_trace.get("reduced_training_executed")), "full_model_training_executed": bool(training_trace.get("full_model_training_executed")), "loss_decreased": loss_delta > 0.0, "target_metric_match": target.get("metric") == "loss_delta", "proxy_declared": bool(target.get("proxy"))}
    return {"accuracy_before": before, "accuracy_after": after, "accuracy_delta": after-before, "loss_before": loss_before, "loss_after": loss_after, "loss_delta": loss_delta, "examples": [{"task_id": item.get("task_id"), "label": label, "before": b, "after": a} for item,label,b,a in zip(heldout,labels,before_predictions,after_predictions)], "mechanism_checks": checks}

def main():
    p=argparse.ArgumentParser(); [p.add_argument(x, required=True) for x in ["--heldout","--before","--after","--audit","--trace","--target","--output"]]; a=p.parse_args()
    def r(path):
        with open(path, encoding="utf-8") as h: return json.load(h)
    with open(a.output,"w",encoding="utf-8") as h: json.dump(evaluate(r(a.heldout),r(a.before),r(a.after),r(a.audit),r(a.trace),r(a.target)),h,indent=2,sort_keys=True)
if __name__ == "__main__": main()
