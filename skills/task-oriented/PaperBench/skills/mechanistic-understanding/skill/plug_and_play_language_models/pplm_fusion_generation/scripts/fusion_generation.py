import math

def softmax(logits):
    m=max(logits); e=[math.exp(v-m) for v in logits]; s=sum(e); return [v/s for v in e]

def geometric_fuse(base_logits, perturbed_logits, gm_scale=0.9):
    if not 0.0 <= gm_scale <= 1.0: raise ValueError('gm_scale must be in [0,1]')
    b=softmax(base_logits); p=softmax(perturbed_logits); eps=1e-12
    raw=[(max(bi,eps)**(1-gm_scale))*(max(pi,eps)**gm_scale) for bi,pi in zip(b,p)]
    s=sum(raw); fused=[x/s for x in raw]
    token=max(range(len(fused)), key=lambda i:fused[i])
    ent=-sum(x*math.log(max(x,eps)) for x in fused)
    return {'base_probs':b,'perturbed_probs':p,'fused_probs':fused,'selected_index':token,'entropy':ent}
