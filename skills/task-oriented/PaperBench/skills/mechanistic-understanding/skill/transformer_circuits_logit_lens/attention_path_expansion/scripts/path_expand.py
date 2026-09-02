#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path


def matmul(a,b):
    if len(a[0]) != len(b): raise ValueError('incompatible matrix shapes')
    return [[sum(row[k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for row in a]

def select_rows(m, ids): return [m[i] for i in ids]

def max_abs_diff(a,b): return max(abs(a[i][j]-b[i][j]) for i in range(len(a)) for j in range(len(a[0]))) if a else 0.0

def add(a,b): return [[a[i][j]+b[i][j] for j in range(len(a[0]))] for i in range(len(a))]

def head_output(residual, attention, ov): return matmul(matmul(attention, residual), ov)

def analyze(data):
    residual=select_rows(data['embedding'], data['tokens'])
    unembedding=data['unembedding']; atts=data['attention_patterns']; ovs=data['ov_matrices']
    direct=matmul(residual, unembedding)
    first=[]
    for a,ov in zip(atts,ovs): first.append(matmul(head_output(residual,a,ov), unembedding))
    result={'direct_logits':direct,'first_order_logits':first}
    if len(atts) >= 2:
        h1=head_output(residual,atts[0],ovs[0])
        explicit_h2=head_output(add(residual,h1),atts[1],ovs[1])
        explicit=matmul(add(add(residual,h1),explicit_h2),unembedding)
        h2_first=head_output(residual,atts[1],ovs[1])
        virtual=head_output(h1,atts[1],ovs[1])
        expanded=matmul(add(add(add(residual,h1),h2_first),virtual),unembedding)
        result.update({'virtual_logits':matmul(virtual,unembedding),'explicit_logits':explicit,'expanded_logits':expanded,'max_consistency_error':max_abs_diff(explicit,expanded)})
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    Path(args.output).write_text(json.dumps(analyze(json.loads(Path(args.input).read_text())),indent=2)+'\n')
if __name__=='__main__': main()
