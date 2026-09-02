import json, math

def _check_dist(dist):
    if not dist or any(x < 0 for x in dist): raise ValueError("invalid policy distribution")
    s=sum(dist)
    if abs(s-1.0)>1e-6: raise ValueError("policy distribution must sum to one")

def validate_unroll(unroll):
    rewards=unroll["rewards"]; actions=unroll["actions"]; discounts=unroll["discounts"]
    values=unroll["values"]; target=unroll["target_policy"]; behavior=unroll["behavior_policy"]
    n=len(rewards)
    if n==0 or len(actions)!=n or len(discounts)!=n or len(target)!=n or len(behavior)!=n: raise ValueError("inconsistent unroll lengths")
    if len(values)!=n+1: raise ValueError("values must include bootstrap")
    target_probs=[]; behavior_probs=[]; lags=[]
    for a,tp,bp in zip(actions,target,behavior):
        _check_dist(tp); _check_dist(bp)
        if a<0 or a>=len(tp) or a>=len(bp): raise ValueError("action out of range")
        if bp[a] <= 0: raise ValueError("behavior action probability must be positive")
        target_probs.append(tp[a]); behavior_probs.append(bp[a]); lags.append(abs(tp[a]-bp[a]))
    return {"rewards":rewards,"discounts":discounts,"actions":actions,"values":values,"target_action_probs":target_probs,"behavior_action_probs":behavior_probs,"policy_lag_mean":sum(lags)/len(lags),"has_policy_lag":any(x>1e-9 for x in lags)}

def main(path):
    data=json.load(open(path))
    print(json.dumps(validate_unroll(data), indent=2))
if __name__=='__main__':
    import sys; main(sys.argv[1])
