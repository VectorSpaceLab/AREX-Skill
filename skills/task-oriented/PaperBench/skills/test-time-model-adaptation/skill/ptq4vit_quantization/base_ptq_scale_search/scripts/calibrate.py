import math

def uniform_quantize(values, scale, bits=8):
    if scale <= 0: raise ValueError('scale must be positive')
    qmax=2**(bits-1)-1
    qmin=-qmax
    return [max(qmin,min(qmax,round(v/scale)))*scale for v in values]

def mse(a,b):
    return sum((x-y)**2 for x,y in zip(a,b))/len(a)

def cosine_distance(a,b):
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return 1.0 - dot/(na*nb+1e-12)

def search_scale(values, candidates, bits=8, metric=mse):
    trace=[]
    for scale in candidates:
        recon=uniform_quantize(values, scale, bits)
        score=metric(values,recon)
        trace.append({'scale':scale,'score':score})
    best=min(trace, key=lambda x:x['score'])
    return {'scale':best['scale'],'score':best['score'],'trace':trace,'reconstruction':uniform_quantize(values,best['scale'],bits)}
