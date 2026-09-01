import math

def _softmax(x):
    m=max(x); e=[math.exp(v-m) for v in x]; s=sum(e); return [v/s for v in e]

def _kl(p,q,eps=1e-12):
    return sum(pi*math.log(max(pi,eps)/max(qi,eps)) for pi,qi in zip(p,q))

def run_perturbation(base_logits, objective_fn, steps=5, step_size=0.5, kl_scale=0.0, normalize=True):
    perturb=[0.0 for _ in base_logits]; trace=[]; base_probs=_softmax(base_logits)
    for step in range(steps):
        current=[b+p for b,p in zip(base_logits, perturb)]
        out=objective_fn(current); grad=list(out['gradient'])
        probs=_softmax(current)
        if kl_scale:
            grad=[g + kl_scale*(pi-bi) for g,pi,bi in zip(grad,probs,base_probs)]
        norm=math.sqrt(sum(g*g for g in grad)) or 1.0
        used=[g/norm for g in grad] if normalize else grad
        before=list(perturb)
        perturb=[p-step_size*g for p,g in zip(perturb, used)]
        after_logits=[b+p for b,p in zip(base_logits, perturb)]
        after=objective_fn(after_logits)
        trace.append({'step':step,'loss_before':out['loss'],'loss_after':after['loss'],'target_mass_before':out.get('target_mass'),'target_mass_after':after.get('target_mass'),'kl_after':_kl(_softmax(after_logits),base_probs),'params_before':before,'params_after':list(perturb)})
    return {'perturbation':perturb,'perturbed_logits':[b+p for b,p in zip(base_logits,perturb)],'trace':trace,'optimizer_step_executed': steps>0 and any(abs(v)>1e-12 for v in perturb)}
