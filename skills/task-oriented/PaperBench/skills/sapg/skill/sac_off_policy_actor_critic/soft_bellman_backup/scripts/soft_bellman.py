import argparse, json

def soft_values(q_values, log_probs, alpha=1.0):
    if len(q_values) != len(log_probs):
        raise ValueError("q_values and log_probs must align")
    return [float(q)-float(alpha)*float(lp) for q,lp in zip(q_values, log_probs)]

def q_targets(rewards, dones, next_soft_values, gamma=0.99):
    if not (len(rewards)==len(dones)==len(next_soft_values)):
        raise ValueError("rewards, dones, and next_soft_values must align")
    return [float(r)+(0.0 if bool(d) else float(gamma)*float(v)) for r,d,v in zip(rewards,dones,next_soft_values)]

def mse(values, targets):
    return sum((float(v)-float(t))**2 for v,t in zip(values, targets))/len(values)

def backup_report(q_values, log_probs, rewards, dones, next_soft_values, gamma=0.99, alpha=1.0):
    vals=soft_values(q_values, log_probs, alpha)
    targets=q_targets(rewards, dones, next_soft_values, gamma)
    return {"soft_values": vals, "q_targets": targets, "q_loss": mse(q_values, targets)}

def main():
    p=argparse.ArgumentParser()
    for n in ['q-values','log-probs','rewards','dones','next-soft-values']:
        p.add_argument('--'+n, required=True)
    p.add_argument('--gamma', type=float, default=0.99); p.add_argument('--alpha', type=float, default=1.0)
    a=p.parse_args()
    print(json.dumps(backup_report(json.loads(a.q_values), json.loads(a.log_probs), json.loads(a.rewards), json.loads(a.dones), json.loads(a.next_soft_values), a.gamma, a.alpha), indent=2))
if __name__=='__main__': main()
