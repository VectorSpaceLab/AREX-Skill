import math

def softmax(logits):
    m=max(logits.values())
    exps={k: math.exp(v-m) for k,v in logits.items()}
    z=sum(exps.values())
    return {k:v/z for k,v in exps.items()}

def fudge_rescore(prefix_tokens, base_logits, future_probs, strength=1.0, top_k=None, eps=1e-6):
    items=sorted(base_logits.items(), key=lambda kv: kv[1], reverse=True)
    if top_k is not None:
        items=items[:top_k]
    adjusted={}; trace={}
    for tok, base in items:
        if tok not in future_probs:
            raise KeyError(f"missing future probability for {tok}")
        p=min(1.0-eps, max(eps, float(future_probs[tok])))
        fl=math.log(p)
        adj=float(base)+strength*fl
        adjusted[tok]=adj
        trace[tok]={"prefix_tokens": list(prefix_tokens), "candidate": tok, "base_logit": float(base), "future_probability": p, "future_log_score": fl, "adjusted_logit": adj}
    probs=softmax(adjusted)
    for tok,p in probs.items(): trace[tok]["probability"]=p
    return {"probabilities": probs, "trace": trace}
