def hessian_score(reference, candidate, gradients):
    if not (len(reference)==len(candidate)==len(gradients)): raise ValueError('length mismatch')
    return sum(((c-r)**2)*(g**2) for r,c,g in zip(reference,candidate,gradients))/len(reference)

def rank_candidates(reference, candidates, gradients):
    scored=[{'name':name,'score':hessian_score(reference,values,gradients),'values':values} for name,values in candidates]
    return sorted(scored, key=lambda x:x['score'])

def weighted_loss_and_grad(scale, values, target, gradients):
    pred=[scale*v for v in values]
    loss=sum(((p-t)**2)*(g**2) for p,t,g in zip(pred,target,gradients))/len(values)
    grad=sum(2*(p-t)*v*(g**2) for p,t,g,v in zip(pred,target,gradients,values))/len(values)
    return loss, grad
