import math

def transform(x, source_dim, mask, theta, bound=False):
    if len(x)>source_dim: raise ValueError('target dimension exceeds source dimension')
    if len(mask)!=source_dim or len(theta)!=source_dim: raise ValueError('mask/theta length mismatch')
    out=[0.0]*source_dim
    for i,v in enumerate(x): out[i]=float(v)
    for i,m in enumerate(mask):
        if m:
            val=math.tanh(theta[i]) if bound else theta[i]
            out[i]+=float(val)
    return out

def trainable_count(mask): return sum(1 for v in mask if v)
