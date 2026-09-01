import math
def _argmax(logits): return max(logits.items(), key=lambda kv: (kv[1], kv[0]))[0]
def adjust_logits(context_logits, prior_logits, alpha=1.0):
    if set(context_logits) != set(prior_logits): raise ValueError(f"logit vocabularies differ: {sorted(set(context_logits)^set(prior_logits))}")
    alpha=float(alpha); adjusted={tok:(1.0+alpha)*float(context_logits[tok])-alpha*float(prior_logits[tok]) for tok in context_logits}
    diagnostics={"alpha":alpha,"regular_argmax":_argmax({k:float(v) for k,v in context_logits.items()}),"prior_argmax":_argmax({k:float(v) for k,v in prior_logits.items()}),"adjusted_argmax":_argmax(adjusted)}
    diagnostics["argmax_changed"]=diagnostics["regular_argmax"]!=diagnostics["adjusted_argmax"]
    return adjusted, diagnostics
def softmax(logits):
    m=max(logits.values()); exps={k:math.exp(v-m) for k,v in logits.items()}; total=sum(exps.values()); return {k:v/total for k,v in exps.items()}
