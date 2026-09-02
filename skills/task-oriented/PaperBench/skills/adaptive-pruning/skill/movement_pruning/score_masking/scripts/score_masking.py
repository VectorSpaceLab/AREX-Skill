import argparse,json,math

def _shape(scores):
    if scores and isinstance(scores[0], list): return (len(scores), len(scores[0]))
    return (len(scores),)

def _flatten(scores):
    if scores and isinstance(scores[0], list):
        width=len(scores[0]); out=[]
        for row in scores:
            if len(row)!=width: raise ValueError('scores must be rectangular')
            out += [float(x) for x in row]
        return out,(len(scores),width)
    return [float(x) for x in scores], (len(scores),)

def _unflatten(vals, shape):
    if len(shape)==1: return vals
    r,c=shape; return [vals[i*c:(i+1)*c] for i in range(r)]

def compute_mask(scores, mode='top_v', keep_ratio=None, threshold=None):
    flat, shape = _flatten(scores); n=len(flat); keep=[0]*n
    if mode=='top_v':
        if keep_ratio is None: raise ValueError('keep_ratio required')
        k=max(0,min(n, math.ceil(n*float(keep_ratio))))
        order=sorted(range(n), key=lambda i:(-flat[i], i))
        for i in order[:k]: keep[i]=1
        meta={'mode':mode,'total':n,'kept':sum(keep),'keep_ratio':sum(keep)/n if n else 0,'requested_keep_ratio':keep_ratio,'cutoff_score': flat[order[k-1]] if k else None}
    elif mode=='threshold':
        if threshold is None: raise ValueError('threshold required')
        keep=[1 if x>float(threshold) else 0 for x in flat]
        meta={'mode':mode,'total':n,'kept':sum(keep),'keep_ratio':sum(keep)/n if n else 0,'threshold':threshold}
    else: raise ValueError('unknown mode')
    return {'mask':_unflatten(keep,shape),'metadata':meta,'kept_indices':[i for i,v in enumerate(keep) if v]}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--scores', required=True); p.add_argument('--mode', default='top_v'); p.add_argument('--keep-ratio', type=float); p.add_argument('--threshold', type=float)
    a=p.parse_args(); print(json.dumps(compute_mask(json.loads(a.scores), a.mode, a.keep_ratio, a.threshold), indent=2))
