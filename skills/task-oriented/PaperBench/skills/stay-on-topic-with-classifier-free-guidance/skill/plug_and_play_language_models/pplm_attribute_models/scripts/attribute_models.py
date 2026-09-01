
from math import exp, log

def softmax(logits):
    m=max(logits); ex=[exp(x-m) for x in logits]; s=sum(ex); return [x/s for x in ex]

def bow_loss(probs, vocab, target_words, eps=1e-12):
    idx=[vocab.index(w) for w in target_words if w in vocab]
    mass=sum(probs[i] for i in idx)
    return -log(max(mass, eps)), {"matched_terms":[vocab[i] for i in idx], "target_mass":mass}

def linear_score(vec, weights, bias=0.0):
    return sum(v*w for v,w in zip(vec,weights))+bias
