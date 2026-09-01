import math

def softmax(logits):
    m=max(logits); ex=[math.exp(x-m) for x in logits]; s=sum(ex); return [x/s for x in ex]

def bow_loss_and_grad(tokens, logits, target_words, eps=1e-12):
    idx=[i for i,t in enumerate(tokens) if t in set(target_words)]
    if not idx:
        raise ValueError('no target_words are present in tokens')
    p=softmax(logits); mass=sum(p[i] for i in idx); mass=max(mass, eps)
    grad=[]
    for j,pj in enumerate(p):
        indicator=1.0 if j in idx else 0.0
        grad.append(pj - (pj*indicator/mass))
    return {'loss': -math.log(mass), 'gradient': grad, 'target_mass': mass, 'probabilities': p, 'target_indices': idx}
