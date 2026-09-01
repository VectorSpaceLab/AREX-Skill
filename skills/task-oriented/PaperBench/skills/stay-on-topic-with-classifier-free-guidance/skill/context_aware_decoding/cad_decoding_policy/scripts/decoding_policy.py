import math, random
def probabilities(logits):
    m=max(logits.values()); exps={k:math.exp(float(v)-m) for k,v in logits.items()}; total=sum(exps.values()); return {k:v/total for k,v in exps.items()}
def select_token(logits, mode="greedy", top_p=0.9, seed=0):
    if not logits: raise ValueError("logits must be non-empty")
    probs=probabilities(logits); ordered=sorted(probs.items(), key=lambda kv:(-kv[1],kv[0]))
    if mode=="greedy": return {"mode":mode,"selected":ordered[0][0],"probabilities":probs,"candidates":[ordered[0][0]]}
    if mode!="top_p": raise ValueError("mode must be greedy or top_p")
    cum=0.0; candidates=[]
    for tok,p in ordered:
        candidates.append((tok,p)); cum+=p
        if cum>=top_p: break
    rng=random.Random(seed); r=rng.random()*sum(p for _,p in candidates); acc=0.0; selected=candidates[-1][0]
    for tok,p in candidates:
        acc+=p
        if r<=acc: selected=tok; break
    return {"mode":mode,"selected":selected,"probabilities":probs,"candidates":[t for t,_ in candidates],"top_p":top_p,"seed":seed}
