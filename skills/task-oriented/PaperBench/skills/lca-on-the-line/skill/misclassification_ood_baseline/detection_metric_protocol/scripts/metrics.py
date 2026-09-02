#!/usr/bin/env python3
import argparse, json

def _check(labels, scores):
    if len(labels) != len(scores) or not labels:
        raise ValueError('labels and scores must have equal nonzero length')
    labels=[int(x) for x in labels]
    if any(x not in (0,1) for x in labels):
        raise ValueError('labels must be binary 0/1')
    if len(set(labels)) != 2:
        raise ValueError('AUROC requires both positive and negative labels')
    return labels, [float(x) for x in scores]

def auroc(labels, scores):
    labels, scores=_check(labels, scores)
    pos=[s for y,s in zip(labels,scores) if y==1]
    neg=[s for y,s in zip(labels,scores) if y==0]
    wins=0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins/(len(pos)*len(neg))

def average_precision(labels, scores):
    labels, scores=_check(labels, scores)
    order=sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    positives=sum(labels)
    hit=0; total=0.0
    for rank,i in enumerate(order, start=1):
        if labels[i] == 1:
            hit += 1
            total += hit/rank
    return total/positives

def evaluate(labels, scores, protocol='detector'):
    labels, scores=_check(labels, scores)
    return {'protocol': protocol, 'count': len(labels), 'positive_count': sum(labels), 'base_rate': sum(labels)/len(labels), 'auroc': auroc(labels, scores), 'aupr': average_precision(labels, scores)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input_json')
    ap.add_argument('--output', required=True)
    ap.add_argument('--protocol', default='detector')
    args=ap.parse_args()
    data=json.load(open(args.input_json))
    json.dump(evaluate(data['labels'], data['scores'], args.protocol), open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
