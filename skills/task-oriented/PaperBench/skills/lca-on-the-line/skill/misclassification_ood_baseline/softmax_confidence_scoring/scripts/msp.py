#!/usr/bin/env python3
import argparse, json, math

def _finite(row):
    return all(isinstance(x, (int, float)) and math.isfinite(float(x)) for x in row)

def is_probability_vector(row, tol=1e-6):
    return bool(row) and _finite(row) and all(float(x) >= 0 for x in row) and abs(sum(float(x) for x in row) - 1.0) <= tol

def softmax(row):
    if not row or not _finite(row):
        raise ValueError('row must be non-empty and finite')
    m=max(float(x) for x in row)
    exps=[math.exp(float(x)-m) for x in row]
    total=sum(exps)
    return [x/total for x in exps]

def score_rows(rows, mode='auto'):
    out=[]
    for idx,row in enumerate(rows):
        if mode == 'probabilities' or (mode == 'auto' and is_probability_vector(row)):
            probs=[float(x) for x in row]
        elif mode in {'logits','auto'}:
            probs=softmax(row)
        else:
            raise ValueError('mode must be logits, probabilities, or auto')
        pred=max(range(len(probs)), key=lambda i: probs[i])
        out.append({'index': idx, 'predicted_class': pred, 'msp': probs[pred], 'probabilities': probs})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input_json')
    ap.add_argument('--mode', default='auto')
    ap.add_argument('--output', required=True)
    args=ap.parse_args()
    rows=json.load(open(args.input_json))
    result={'scores': score_rows(rows, args.mode)}
    result['mean_msp']=sum(x['msp'] for x in result['scores'])/len(result['scores']) if result['scores'] else 0.0
    json.dump(result, open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
