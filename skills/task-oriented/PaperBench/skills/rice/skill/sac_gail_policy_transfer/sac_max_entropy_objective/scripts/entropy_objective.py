#!/usr/bin/env python3
import argparse, json, math

def _validate(values, name):
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    out=[]
    for value in values:
        number=float(value)
        if not math.isfinite(number):
            raise ValueError(f"{name} contains non-finite value")
        out.append(number)
    return out

def compute_entropy_objective(q_values, log_probs, alpha=1.0):
    q=_validate(q_values, 'q_values')
    logs=_validate(log_probs, 'log_probs')
    if len(q)!=len(logs):
        raise ValueError('q_values and log_probs must have equal length')
    alpha=float(alpha)
    soft=[qi - alpha*lp for qi, lp in zip(q, logs)]
    actor=[alpha*lp - qi for qi, lp in zip(q, logs)]
    return {'soft_values': soft, 'actor_losses': actor, 'mean_soft_value': sum(soft)/len(soft), 'mean_actor_loss': sum(actor)/len(actor), 'alpha': alpha}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    data=json.load(open(args.input))
    result=compute_entropy_objective(data['q_values'], data['log_probs'], data.get('alpha',1.0))
    json.dump(result, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
