#!/usr/bin/env python3
import argparse, json, math

def normal_logpdf(x, mean, std):
    return -0.5*((x-mean)/std)**2 - math.log(std) - 0.5*math.log(2*math.pi)

def logits(atoms, obs, params, prior_log_probs, proposal_log_probs):
    w,b=params['w'],params['b']
    scores=[w*(-(a-obs)**2)+b*a for a in atoms]
    return [s+q-p for s,p,q in zip(scores, prior_log_probs, proposal_log_probs)]

def softmax(xs):
    m=max(xs); ws=[math.exp(x-m) for x in xs]; total=sum(ws); return [w/total for w in ws]

def loss_and_grad(atoms, obs, positive_index, params, prior_log_probs, proposal_log_probs):
    lg=logits(atoms, obs, params, prior_log_probs, proposal_log_probs)
    probs=softmax(lg)
    loss=-math.log(max(probs[positive_index], 1e-300))
    grad_w=0.0; grad_b=0.0
    for i,a in enumerate(atoms):
        target=1.0 if i == positive_index else 0.0
        diff=probs[i]-target
        grad_w += diff * (-(a-obs)**2)
        grad_b += diff * a
    return loss, probs, {'w': grad_w, 'b': grad_b}

def one_step(atoms, obs, positive_index, params, prior_log_probs, proposal_log_probs, lr=0.2):
    before=dict(params)
    loss_before, probs_before, grad = loss_and_grad(atoms, obs, positive_index, before, prior_log_probs, proposal_log_probs)
    after={'w': before['w'] - lr*grad['w'], 'b': before['b'] - lr*grad['b']}
    loss_after, probs_after, _ = loss_and_grad(atoms, obs, positive_index, after, prior_log_probs, proposal_log_probs)
    return {'loss_before': loss_before, 'loss_after': loss_after, 'params_before': before, 'params_after': after, 'prob_positive_before': probs_before[positive_index], 'prob_positive_after': probs_after[positive_index], 'optimizer_state_changed': before != after}


def learning_rate_sweep(atoms, obs, positive_index, params, prior_log_probs, proposal_log_probs, rates):
    return [{'lr': lr, **one_step(atoms, obs, positive_index, dict(params), prior_log_probs, proposal_log_probs, lr=lr)} for lr in rates]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test', action='store_true'); ns=ap.parse_args()
    atoms=[-1.0, 0.4, 1.5]; obs=0.5; p=[normal_logpdf(a,0,1) for a in atoms]; q=[normal_logpdf(a,0.4,0.7) for a in atoms]
    out=one_step(atoms, obs, 1, {'w':0.1,'b':0.0}, p, q, lr=0.5)
    if ns.self_test:
        assert out['loss_after'] < out['loss_before']; assert out['params_before'] != out['params_after']
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
