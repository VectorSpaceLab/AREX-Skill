import argparse, json

def discounted_sum(values, gamma):
    total=0.0
    weight=1.0
    for value in values:
        total += weight * float(value)
        weight *= float(gamma)
    return total

def soft_objective(rewards, log_probs, gamma=0.99, alpha=1.0):
    if len(rewards) != len(log_probs):
        raise ValueError("rewards and log_probs must have the same length")
    entropy_bonuses=[-float(lp)*float(alpha) for lp in log_probs]
    soft_rewards=[float(r)+b for r,b in zip(rewards, entropy_bonuses)]
    return {"reward_return": discounted_sum(rewards,gamma), "soft_return": discounted_sum(soft_rewards,gamma), "entropy_bonuses": entropy_bonuses}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rewards', required=True)
    p.add_argument('--log-probs', required=True)
    p.add_argument('--gamma', type=float, default=0.99)
    p.add_argument('--alpha', type=float, default=1.0)
    a=p.parse_args()
    print(json.dumps(soft_objective(json.loads(a.rewards), json.loads(a.log_probs), a.gamma, a.alpha), indent=2))
if __name__=='__main__': main()
