import math

def aggregate(probs, groups):
    used=[]
    out=[]
    for g in groups:
        if not g: raise ValueError('empty group')
        for idx in g:
            if idx in used: raise ValueError('overlapping source labels')
            if idx<0 or idx>=len(probs): raise ValueError('label index out of range')
            used.append(idx)
        out.append(sum(probs[i] for i in g)/len(g))
    s=sum(out)
    return [v/s for v in out] if s else [1/len(out)]*len(out)

def softmax(xs):
    m=max(xs); ex=[math.exp(x-m) for x in xs]; s=sum(ex); return [v/s for v in ex]

def linear_head(logits, weights, bias):
    scores=[]
    for row,b in zip(weights,bias): scores.append(sum(a*bw for a,bw in zip(logits,row))+b)
    return softmax(scores)
