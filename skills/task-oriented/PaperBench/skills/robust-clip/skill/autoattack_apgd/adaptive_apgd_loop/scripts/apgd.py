import math
from projection import project
from dlr import dlr_loss

def predict(logits):
    return max(range(len(logits)), key=lambda i: logits[i])

def finite_diff_grad(loss_fn, x, h=1e-5):
    grad=[]
    for i in range(len(x)):
        xp=list(x); xm=list(x); xp[i]+=h; xm[i]-=h
        grad.append((loss_fn(xp)-loss_fn(xm))/(2*h))
    return grad

def run_apgd(logit_fn, examples, labels, norm='Linf', eps=0.35, iterations=20, step_size=None, window=4, loss_name='dlr', restart_directions=None):
    step_size = step_size if step_size is not None else 2.0*eps/max(iterations,1)**0.5
    restart_directions = restart_directions or []
    advs=[]; successes=[]; traces=[]; events=[]
    for idx,(x,y) in enumerate(zip(examples, labels)):
        adv=list(x); best=list(x); best_loss=-1e9; losses=[]; local_step=step_size
        def loss_at(z):
            logits=logit_fn(z)
            if loss_name == 'dlr': return dlr_loss(logits,y)
            exps=[math.exp(v-max(logits)) for v in logits]; prob=exps[y]/sum(exps)
            return -math.log(max(prob,1e-12))
        for it in range(iterations):
            loss=loss_at(adv); losses.append(loss)
            if loss > best_loss: best_loss=loss; best=list(adv)
            grad=finite_diff_grad(loss_at, adv)
            norm_grad=max(abs(g) for g in grad) if norm=='Linf' else math.sqrt(sum(g*g for g in grad))
            if norm_grad == 0: direction=[0.0 for _ in grad]
            elif norm=='Linf': direction=[1.0 if g>=0 else -1.0 for g in grad]
            else: direction=[g/norm_grad for g in grad]
            candidate=[a+local_step*d for a,d in zip(adv,direction)]
            adv,_=project(x,candidate,norm=norm,eps=eps,lower=0.0,upper=1.0)
            if len(losses) >= window and it % window == window-1:
                recent=losses[-window:]
                if max(recent) <= best_loss + 1e-10 or sum(recent[i] < recent[i-1] for i in range(1,len(recent))) >= window//2:
                    old=local_step; local_step*=0.5; adv=list(best)
                    events.append({'example':idx,'iteration':it,'old_step':old,'new_step':local_step,'reason':'non_improving_window'})
        final=best if predict(logit_fn(best)) != y else adv
        for direction in restart_directions:
            candidate=[xi + eps * di for xi, di in zip(x, direction)]
            candidate,_=project(x,candidate,norm=norm,eps=eps,lower=0.0,upper=1.0)
            if loss_at(candidate) > best_loss:
                best_loss=loss_at(candidate); best=list(candidate)
            if predict(logit_fn(candidate)) != y:
                final=candidate
                events.append({'example':idx,'iteration':iterations,'old_step':local_step,'new_step':local_step,'reason':'deterministic_restart_success'})
                break
        advs.append(final); successes.append(predict(logit_fn(final)) != y); traces.append({'losses':losses,'best_loss':best_loss})
    return {'adversarial_examples':advs,'successes':successes,'success_rate':sum(successes)/len(successes),'traces':traces,'step_events':events}
