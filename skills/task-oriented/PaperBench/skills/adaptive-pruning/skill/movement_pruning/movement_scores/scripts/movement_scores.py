import argparse,json

def _flat(x):
    if x and isinstance(x[0], list): return [float(v) for r in x for v in r], (len(x), len(x[0]))
    return [float(v) for v in x], (len(x),)
def _unflat(v, shape):
    if len(shape)==1: return v
    r,c=shape; return [v[i*c:(i+1)*c] for i in range(r)]

def update_movement_scores(weights, scores, gradients, lr_score=1.0, lr_weight=1.0):
    w,sh=_flat(weights); s,sh2=_flat(scores); g,sh3=_flat(gradients)
    if sh!=sh2 or sh!=sh3: raise ValueError('shape mismatch')
    new=[]; diag=[]
    for i,(wi,si,gi) in enumerate(zip(w,s,g)):
        grad_s=gi*wi; sn=si-float(lr_score)*grad_s
        wa=wi-float(lr_weight)*gi
        away=abs(wa)>abs(wi) if wi!=0 else False
        new.append(sn); diag.append({'index':i,'weight':wi,'gradient':gi,'score_gradient':grad_s,'score_delta':sn-si,'away_from_zero':away,'movement_label':'away' if away else 'toward_or_neutral'})
    return {'updated_scores':_unflat(new,sh),'diagnostics':diag}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--weights',required=True); p.add_argument('--scores',required=True); p.add_argument('--gradients',required=True); p.add_argument('--lr-score',type=float,default=1.0)
    a=p.parse_args(); print(json.dumps(update_movement_scores(json.loads(a.weights),json.loads(a.scores),json.loads(a.gradients),a.lr_score), indent=2))
