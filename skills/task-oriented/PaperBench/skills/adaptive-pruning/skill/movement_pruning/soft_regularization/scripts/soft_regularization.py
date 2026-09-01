import argparse,json,math

def _flat(x):
    if x and isinstance(x[0], list): return [float(v) for r in x for v in r], (len(x), len(x[0]))
    return [float(v) for v in x], (len(x),)
def _unflat(v, shape):
    if len(shape)==1: return v
    r,c=shape; return [v[i*c:(i+1)*c] for i in range(r)]
def sigmoid(x):
    if x>=0:
        z=math.exp(-x); return 1/(1+z)
    z=math.exp(x); return z/(1+z)
def soft_movement_regularization(scores, lambda_mvp=1.0, threshold=None, lr=1.0):
    flat,sh=_flat(scores); lam=float(lambda_mvp); sig=[sigmoid(x) for x in flat]; grad=[lam*v*(1-v) for v in sig]; after=[x-float(lr)*g for x,g in zip(flat,grad)]
    out={'penalty':lam*sum(sig),'gradient':_unflat(grad,sh),'sigmoid_mass':sum(sig),'scores_after_reg_step':_unflat(after,sh)}
    if threshold is not None:
        t=float(threshold); out['threshold_diagnostics']={'keep_before':sum(x>t for x in flat)/len(flat),'keep_after':sum(x>t for x in after)/len(after)}
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--scores',required=True); p.add_argument('--lambda-mvp',type=float,default=1.0); p.add_argument('--threshold',type=float); p.add_argument('--lr',type=float,default=1.0)
    a=p.parse_args(); print(json.dumps(soft_movement_regularization(json.loads(a.scores),a.lambda_mvp,a.threshold,a.lr), indent=2))
