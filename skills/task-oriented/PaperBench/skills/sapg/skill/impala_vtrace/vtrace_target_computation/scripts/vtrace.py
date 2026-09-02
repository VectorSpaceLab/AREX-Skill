from math import isfinite

def validate_lengths(rewards, discounts, values, target_probs, behavior_probs):
    n=len(rewards)
    if n==0: raise ValueError("trajectory must be non-empty")
    if len(discounts)!=n or len(target_probs)!=n or len(behavior_probs)!=n: raise ValueError("trajectory fields must share length")
    if len(values)!=n+1: raise ValueError("values must include bootstrap value")
    for p in behavior_probs:
        if p<=0: raise ValueError("behavior probabilities must be positive")
    for p in target_probs:
        if p<0: raise ValueError("target probabilities must be non-negative")
    for d in discounts:
        if d<0: raise ValueError("discounts must be non-negative")

def compute_vtrace(rewards, discounts, values, target_probs, behavior_probs, rho_bar=1.0, c_bar=1.0):
    validate_lengths(rewards, discounts, values, target_probs, behavior_probs)
    if rho_bar <= 0 or c_bar <= 0: raise ValueError("clip thresholds must be positive")
    ratios=[t/b for t,b in zip(target_probs, behavior_probs)]
    rhos=[min(rho_bar,r) for r in ratios]
    cs=[min(c_bar,r) for r in ratios]
    n=len(rewards)
    targets=[0.0]*n
    next_v=values[-1]
    for i in range(n-1,-1,-1):
        delta=rhos[i]*(rewards[i]+discounts[i]*values[i+1]-values[i])
        targets[i]=values[i]+delta+discounts[i]*cs[i]*(next_v-values[i+1])
        next_v=targets[i]
    advantages=[]
    for i in range(n):
        next_target=targets[i+1] if i+1<n else values[-1]
        advantages.append(rewards[i]+discounts[i]*next_target-values[i])
    return {"ratios":ratios,"rhos":rhos,"cs":cs,"targets":targets,"advantages":advantages}
