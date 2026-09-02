import argparse, json, math

def evaluate(params, state, noise, target_action=1.0, alpha=0.2):
    mean=float(params['mean_weight'])*float(state)
    std=math.exp(float(params['log_std']))
    action=mean+std*float(noise)
    log_prob=-0.5*float(noise)**2-float(params['log_std'])-0.5*math.log(2*math.pi)
    q_value=-(action-float(target_action))**2
    loss=float(alpha)*log_prob-q_value
    return {"mean":mean,"std":std,"action":action,"log_prob":log_prob,"q_value":q_value,"policy_loss":loss}

def actor_update(params, state, noise, target_action=1.0, alpha=0.2, lr=0.05):
    before=dict(params)
    ev=evaluate(params,state,noise,target_action,alpha)
    action=ev['action']; std=ev['std']; diff=action-float(target_action)
    grad_mean=2*diff*float(state)
    grad_log_std=2*diff*std*float(noise)-float(alpha)
    after={"mean_weight": float(params['mean_weight'])-float(lr)*grad_mean, "log_std": float(params['log_std'])-float(lr)*grad_log_std}
    after_eval=evaluate(after,state,noise,target_action,alpha)
    return {"params_before":before,"params_after":after,"loss_before":ev['policy_loss'],"loss_after":after_eval['policy_loss'],"action_before":action,"action_after":after_eval['action']}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--params', required=True); p.add_argument('--state', type=float, default=1.0); p.add_argument('--noise', type=float, default=0.0); p.add_argument('--target-action', type=float, default=1.0); p.add_argument('--alpha', type=float, default=0.2); p.add_argument('--lr', type=float, default=0.05)
    a=p.parse_args(); print(json.dumps(actor_update(json.loads(a.params),a.state,a.noise,a.target_action,a.alpha,a.lr), indent=2))
if __name__=='__main__': main()
