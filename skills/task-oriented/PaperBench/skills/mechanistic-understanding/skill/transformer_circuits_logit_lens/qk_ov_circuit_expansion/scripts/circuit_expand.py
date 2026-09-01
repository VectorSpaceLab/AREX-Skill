#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path


def transpose(a): return [list(col) for col in zip(*a)]

def matmul(a,b):
    if len(a[0]) != len(b): raise ValueError('incompatible matrix shapes')
    return [[sum(row[k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for row in a]

def expand_qk(embedding, w_qk):
    return matmul(matmul(embedding, w_qk), transpose(embedding))

def expand_ov(embedding, w_ov, unembedding):
    return matmul(matmul(embedding, w_ov), unembedding)

def positive_real_eigen_fraction_2x2(m):
    n=len(m)
    if n == 1:
        return 1.0 if m[0][0] > 0 else 0.0
    if n != 2 or len(m[0]) != 2 or len(m[1]) != 2:
        return None
    tr=m[0][0]+m[1][1]; det=m[0][0]*m[1][1]-m[0][1]*m[1][0]
    disc=tr*tr-4*det
    if disc < 0: return 0.0
    r=math.sqrt(disc)
    vals=[(tr+r)/2,(tr-r)/2]
    return sum(1 for v in vals if v > 0)/2

def summarize_copying(m):
    diag=[m[i][i] for i in range(min(len(m), len(m[0])))]
    off=[m[i][j] for i in range(len(m)) for j in range(len(m[0])) if i != j]
    diag_mean=sum(diag)/len(diag) if diag else 0.0
    off_mean=sum(off)/len(off) if off else 0.0
    return {'diagonal_mean':diag_mean,'off_diagonal_mean':off_mean,'diagonal_dominance':diag_mean-off_mean,'positive_real_eigen_fraction':positive_real_eigen_fraction_2x2(m)}

def analyze(data):
    qk=expand_qk(data['embedding'], data['w_qk'])
    ov=expand_ov(data['embedding'], data['w_ov'], data['unembedding'])
    return {'expanded_qk':qk,'expanded_ov':ov,'ov_copying_summary':summarize_copying(ov),'qk_matching_summary':summarize_copying(qk)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    Path(args.output).write_text(json.dumps(analyze(json.loads(Path(args.input).read_text())),indent=2)+'\n')
if __name__=='__main__': main()
