from itertools import product

def _validate(scores, name):
    vals=[float(x) for x in scores]
    if any(x < 0 for x in vals):
        raise ValueError(f"{name} scores must be nonnegative")
    return vals

def _mask_for(scores, keep):
    order=sorted(range(len(scores)), key=lambda i:(scores[i], i))
    prune=set(order[:len(scores)-keep])
    return [0 if i in prune else 1 for i in range(len(scores))]

def search(head_scores, filter_scores, head_cost, filter_cost, budget):
    hs=_validate(head_scores,'head'); fs=_validate(filter_scores,'filter')
    if head_cost <= 0 or filter_cost <= 0: raise ValueError('costs must be positive')
    best=None
    for n in range(len(hs)+1):
        rem=budget-n*head_cost
        if rem < -1e-12: continue
        f=max(0, min(len(fs), int(rem//filter_cost)))
        cost=n*head_cost+f*filter_cost
        if cost-budget > 1e-12: continue
        hm=_mask_for(hs,n); fm=_mask_for(fs,f)
        loss=sum(s for s,m in zip(hs,hm) if m==0)+sum(s for s,m in zip(fs,fm) if m==0)
        cand=(loss, -cost, -(n+f), hm, fm, cost, n, f)
        if best is None or cand < best: best=cand
    if best is None: raise ValueError('no feasible mask')
    loss, neg_cost, _, hm, fm, cost, n, f=best
    return {'head_mask':hm,'filter_mask':fm,'remaining_cost':cost,'pruned_fisher_loss':loss,'remaining_heads':n,'remaining_filters':f}

def exhaustive(head_scores, filter_scores, head_cost, filter_cost, budget):
    hs=list(head_scores); fs=list(filter_scores); best=None
    for hm in product([0,1], repeat=len(hs)):
      for fm in product([0,1], repeat=len(fs)):
        cost=sum(hm)*head_cost+sum(fm)*filter_cost
        if cost <= budget+1e-12:
          loss=sum(s for s,m in zip(hs,hm) if not m)+sum(s for s,m in zip(fs,fm) if not m)
          cand=(loss,-cost,-(sum(hm)+sum(fm)),list(hm),list(fm),cost)
          if best is None or cand < best: best=cand
    return best
