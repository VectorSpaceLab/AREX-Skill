#!/usr/bin/env python3
import argparse, json, math

def matmul(a,b):
    return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]

def transpose(m): return [list(col) for col in zip(*m)]
def active_rank(e, eps=1e-12): return sum(1 for v in e if abs(v)>eps)

def update_matrix(a,e,b):
    ea=[[e[i]*a[i][j] for j in range(len(a[0]))] for i in range(len(e))]
    return matmul(b, ea)

def linear_forward(x, weight, bias=None):
    out=matmul(x, transpose(weight))
    if bias is not None:
        out=[[v+bias[j] for j,v in enumerate(row)] for row in out]
    return out

def svd_forward(x, weight, bias, a, e, b, alpha=1.0, ranknum=None):
    base=linear_forward(x, weight, bias)
    ar=active_rank(e) if ranknum is None else ranknum
    if ar <= 0:
        return {"output": base, "active_rank": 0, "update_matrix": [[0.0 for _ in weight[0]] for __ in weight]}
    upd=update_matrix(a,e,b)
    low=linear_forward(x, upd, None)
    scale=alpha/(ar+1e-5)
    return {"output": [[base[i][j]+scale*low[i][j] for j in range(len(base[0]))] for i in range(len(base))], "active_rank": ar, "update_matrix": upd}

def self_test():
    x=[[1.0,2.0]]; w=[[1.0,0.0],[0.0,1.0]]; a=[[1,0],[0,1]]; b=[[1,0],[0,1]]
    z=svd_forward(x,w,None,a,[0,0],b)
    assert z['output']==[[1.0,2.0]] and z['active_rank']==0
    y=svd_forward(x,w,None,a,[1,2],b,alpha=2.0,ranknum=2)
    assert abs(y['output'][0][0]-2.0)<1e-4 and abs(y['output'][0][1]-6.0)<1e-4
    return True

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--self-test', action='store_true')
    ns=ap.parse_args()
    if ns.self_test:
        print(json.dumps({'ok': self_test()})); return
    data=json.load(open(ns.input)); print(json.dumps(svd_forward(**data), indent=2))
if __name__=='__main__': main()
