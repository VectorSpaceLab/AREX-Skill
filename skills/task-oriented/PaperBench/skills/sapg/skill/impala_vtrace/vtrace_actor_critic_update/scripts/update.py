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

def sigmoid(x):
    import math
    return 1/(1+math.exp(-x))

def model_probs(theta, feature):
    p=sigmoid(theta*feature)
    return [p,1-p]

def evaluate(params, unroll, rho_bar=1.0, c_bar=1.0):
    values=[params["value_weight"]*f for f in unroll["features"]] + [params["value_weight"]*unroll["bootstrap_feature"]]
    target_policy=[model_probs(params["policy_weight"], f) for f in unroll["features"]]
    target_action_probs=[dist[a] for dist,a in zip(target_policy, unroll["actions"])]
    vt=compute_vtrace(unroll["rewards"], unroll["discounts"], values, target_action_probs, unroll["behavior_action_probs"], rho_bar, c_bar)
    value_loss=sum((t-v)**2 for t,v in zip(vt["targets"], values[:-1]))/len(unroll["rewards"])
    policy_loss=-sum(r*a for r,a in zip(vt["rhos"], vt["advantages"]))/len(unroll["rewards"])
    entropy=sum(-sum(p*__import__('math').log(max(p,1e-12)) for p in dist) for dist in target_policy)/len(target_policy)
    total=value_loss+0.1*policy_loss-0.01*entropy
    return {"total_loss":total,"value_loss":value_loss,"policy_loss":policy_loss,"entropy":entropy,"vtrace":vt,"values":values,"target_action_probs":target_action_probs}

def train_one_step(params, unroll, lr=0.05):
    before=evaluate(params, unroll)
    grads={}
    eps=1e-5
    for k in sorted(params):
        p1=dict(params); p2=dict(params); p1[k]+=eps; p2[k]-=eps
        grads[k]=(evaluate(p1,unroll)["total_loss"]-evaluate(p2,unroll)["total_loss"])/(2*eps)
    step=lr
    after_params=dict(params)
    after=None
    for _ in range(8):
        candidate={k:params[k]-step*grads[k] for k in params}
        cand_eval=evaluate(candidate, unroll)
        if cand_eval["total_loss"] <= before["total_loss"]:
            after_params=candidate; after=cand_eval; break
        step*=0.5
    if after is None: after=evaluate(after_params, unroll)
    return {"params_before":params,"params_after":after_params,"gradients":grads,"learning_rate_used":step,"loss_before":before["total_loss"],"loss_after":after["total_loss"],"before":before,"after":after,"optimizer_state_changed":params!=after_params}
