#!/usr/bin/env python3
import argparse, json, math

def corrected_logits(model_log_scores, prior_log_probs, proposal_log_probs):
    if not (len(model_log_scores) == len(prior_log_probs) == len(proposal_log_probs)) or not model_log_scores:
        raise ValueError('all inputs must have the same non-zero length')
    return [float(s) + float(q) - float(p) for s,p,q in zip(model_log_scores, prior_log_probs, proposal_log_probs)]

def softmax(logits):
    m=max(logits)
    weights=[math.exp(v-m) for v in logits]
    total=sum(weights)
    if not math.isfinite(total) or total <= 0:
        raise ValueError('invalid softmax mass')
    return [w/total for w in weights]


def correction_effect(model_log_scores, prior_log_probs, proposal_log_probs):
    corrected = transform(model_log_scores, prior_log_probs, proposal_log_probs)['probabilities']
    uncorrected = softmax([float(v) for v in model_log_scores])
    return {'corrected': corrected, 'uncorrected': uncorrected, 'max_probability_shift': max(abs(a-b) for a,b in zip(corrected, uncorrected))}

def transform(model_log_scores, prior_log_probs, proposal_log_probs):
    logits=corrected_logits(model_log_scores, prior_log_probs, proposal_log_probs)
    return {'corrected_logits': logits, 'probabilities': softmax(logits)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test', action='store_true'); ap.add_argument('--input')
    ns=ap.parse_args()
    if ns.self_test:
        out=transform([0.0, 1.0], [-1.0, -1.0], [-1.0, -2.0])
        assert len(out['probabilities']) == 2 and abs(sum(out['probabilities'])-1) < 1e-12
        print(json.dumps({'ok': True, 'output': out}, indent=2)); return
    data=json.load(open(ns.input))
    print(json.dumps(transform(data['model_log_scores'], data['prior_log_probs'], data['proposal_log_probs']), indent=2))
if __name__ == '__main__': main()
