import math

def compose_constraints(candidate_target_probs, targets, lambda_value=1.0, normalize=True, eps=1e-6):
    if not targets:
        raise ValueError('targets must not be empty')
    weight=float(lambda_value)/(len(targets) if normalize else 1.0)
    scores={}; audit={}
    for cand, probs in candidate_target_probs.items():
        total=0.0; contrib=[]
        for t in targets:
            if t not in probs:
                raise KeyError(f'missing score for {cand}:{t}')
            p=min(1.0-eps, max(eps, float(probs[t])))
            c=weight*math.log(p)
            total += c
            contrib.append({'target': t, 'probability': p, 'weight': weight, 'contribution': c})
        scores[cand]=total; audit[cand]=contrib
    return {'scores': scores, 'audit': audit, 'lambda_value': lambda_value, 'normalized': normalize}
