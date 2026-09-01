import math

def normalized_weights(log_weights):
    m=max(log_weights); vals=[math.exp(w-m) for w in log_weights]; s=sum(vals)
    return [v/s for v in vals]

def effective_sample_size(weights):
    return 1.0/sum(w*w for w in weights)

def fkl_surrogate(log_joint, log_q):
    lw=[a-b for a,b in zip(log_joint,log_q)]
    ws=normalized_weights(lw)
    return sum(w*(lq-lj) for w,lq,lj in zip(ws,log_q,log_joint)), ws, effective_sample_size(ws)

if __name__ == "__main__":
    import json; val,ws,ess=fkl_surrogate([-1,-2],[-1.5,-1.5]); print(json.dumps({"loss":val,"weights":ws,"ess":ess}))
