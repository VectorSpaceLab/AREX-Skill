from __future__ import annotations
import math, json, argparse
from pathlib import Path

def softmax(z):
    m=max(z); e=[math.exp(v-m) for v in z]; s=sum(e); return [v/s for v in e]

def dot(a,b): return sum(x*y for x,y in zip(a,b))

def logits(x,prompt,weights,bias):
    xp=[xi+pi for xi,pi in zip(x,prompt)]
    return [dot(w,xp)+b for w,b in zip(weights,bias)]

def mapping_from_preds(preds, ys, target_labels):
    grouped={t:[] for t in target_labels}
    for p,y in zip(preds,ys): grouped[y].append(p)
    used=set(); mapping={}
    for t in target_labels:
        counts={s:grouped[t].count(s) for s in sorted(set(grouped[t]))}
        candidates=sorted(counts, key=lambda s:(-counts[s],s))
        chosen=next((s for s in candidates if s not in used), candidates[0])
        mapping[t]=chosen; used.add(chosen)
    return mapping

def eval_acc(xs,ys,prompt,weights,bias,mapping):
    inv={v:k for k,v in mapping.items()}; ok=0
    for x,y in zip(xs,ys):
        p=max(range(len(weights)), key=lambda i: logits(x,prompt,weights,bias)[i])
        ok += (inv.get(p)==y)
    return ok/len(xs)

def run_ilm_vp(xs, ys, weights, bias, prompt=None, lr=0.2, epochs=8, iterative=True):
    target_labels=sorted(set(ys)); prompt=list(prompt or [0.0]*len(xs[0]))
    preds0=[max(range(len(weights)), key=lambda i: logits(x,prompt,weights,bias)[i]) for x in xs]
    fixed_mapping=mapping_from_preds(preds0,ys,target_labels)
    mapping=fixed_mapping; hist=[]; losses=[]; p_before=list(prompt)
    for ep in range(epochs):
        if iterative or ep==0:
            preds=[max(range(len(weights)), key=lambda i: logits(x,prompt,weights,bias)[i]) for x in xs]
            mapping=mapping_from_preds(preds,ys,target_labels)
        grad=[0.0]*len(prompt); loss=0.0
        for x,y in zip(xs,ys):
            z=logits(x,prompt,weights,bias); prob=softmax(z); tgt=mapping[y]
            loss += -math.log(max(prob[tgt],1e-12))
            for k in range(len(weights)):
                coeff=prob[k] - (1.0 if k==tgt else 0.0)
                for j in range(len(prompt)): grad[j] += coeff*weights[k][j]
        n=len(xs); prompt=[v-lr*g/n for v,g in zip(prompt,grad)]
        losses.append(loss/n); hist.append(dict(mapping))
    return {'prompt':prompt,'mapping_history':hist,'loss_before':losses[0],'loss_after':losses[-1],'accuracy':eval_acc(xs,ys,prompt,weights,bias,mapping),'fixed_initial_accuracy':eval_acc(xs,ys,p_before,weights,bias,fixed_mapping),'mechanism_checks':{'label_mapping_recomputed':iterative,'optimizer_step_executed':p_before!=prompt,'mapping_changed': any(h!=hist[0] for h in hist[1:]),'source_model_frozen':True}}

def synthetic_problem():
    xs=[[-2,0],[-1.8,.1],[0,2],[.1,1.8],[2,-.2],[1.8,.1]]; ys=['a','a','b','b','c','c']
    weights=[[1,0],[0,1],[-1,0],[0,-1]]; bias=[0,0,0,0]
    return xs,ys,weights,bias

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output', required=True); ap.add_argument('--epochs', type=int, default=8); ap.add_argument('--fixed', action='store_true')
    a=ap.parse_args(); xs,ys,w,b=synthetic_problem(); out=run_ilm_vp(xs,ys,w,b,epochs=a.epochs,iterative=not a.fixed)
    Path(a.output).write_text(json.dumps(out,indent=2)); print(json.dumps(out))
if __name__=='__main__': main()
