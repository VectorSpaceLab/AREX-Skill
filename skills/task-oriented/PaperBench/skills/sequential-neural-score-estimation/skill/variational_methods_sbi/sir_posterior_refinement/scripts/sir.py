import math, random

def normalize(log_weights):
    m=max(log_weights); vals=[math.exp(w-m) for w in log_weights]; s=sum(vals); return [v/s for v in vals]

def sir_resample(samples, log_likelihood, log_prior, log_proposal, n=16, seed=0):
    logw=[ll+lp-lq for ll,lp,lq in zip(log_likelihood,log_prior,log_proposal)]
    weights=normalize(logw); rng=random.Random(seed); out=rng.choices(list(samples), weights=weights, k=n)
    return {"samples":out,"weights":weights,"max_weight":max(weights),"unique":len(set(out))}

if __name__ == "__main__":
    import json; print(json.dumps(sir_resample([0,1,2],[-5,0,-1],[0,0,0],[0,0,0])))
