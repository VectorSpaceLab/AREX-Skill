
from math import exp, log

def softmax(xs):
    m=max(xs); ex=[exp(x-m) for x in xs]; s=sum(ex); return [x/s for x in ex]

def kl(p,q,eps=1e-12):
    return sum(pi*(log(max(pi,eps))-log(max(qi,eps))) for pi,qi in zip(p,q))

def perturb_logits(base_logits, target_indices, steps=8, step_size=1.0, kl_scale=0.05):
    base=list(base_logits); delta=[0.0]*len(base); base_probs=softmax(base)
    trace=[]
    for _ in range(steps):
        probs=softmax([b+d for b,d in zip(base,delta)])
        target_mass=sum(probs[i] for i in target_indices)
        # gradient of -log target mass wrt logits plus approximate KL gradient
        grad=[]
        for j,p in enumerate(probs):
            in_t=1.0 if j in target_indices else 0.0
            g=p - (p*in_t/max(target_mass,1e-12)) + kl_scale*(p-base_probs[j])
            grad.append(g)
        delta=[d-step_size*g for d,g in zip(delta,grad)]
        trace.append({'target_mass':target_mass,'kl':kl(probs,base_probs),'delta_norm':sum(abs(x) for x in delta)})
    final=softmax([b+d for b,d in zip(base,delta)])
    return final, {'params_before':[0.0]*len(base), 'params_after':delta, 'trace':trace, 'base_logits_after':base}
