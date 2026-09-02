#!/usr/bin/env python3
import argparse, json

def abs_mul(a,b):
    if isinstance(a, list): return [abs_mul(x,y) for x,y in zip(a,b)]
    return abs(a*b)
def zeros_like(cur):
    if isinstance(cur, list): return [zeros_like(x) for x in cur]
    return 0.0

def ewma(prev, cur, beta):
    if isinstance(cur, list):
        prev_list = prev if isinstance(prev, list) else zeros_like(cur)
        return [ewma(p, c, beta) for p,c in zip(prev_list, cur)]
    return beta*(prev if isinstance(prev, (int, float)) else 0.0)+(1-beta)*cur
def sub_abs(a,b):
    if isinstance(a, list): return [sub_abs(x,y) for x,y in zip(a,b)]
    return abs(a-b)
def elem_mul(a,b):
    if isinstance(a, list): return [elem_mul(x,y) for x,y in zip(a,b)]
    return a*b
def row_mean(row): return sum(row)/len(row) if row else 0.0
def col_mean(mat, j): return sum(row[j] for row in mat)/len(mat) if mat else 0.0

def update_scores(matrices, state=None, beta1=0.85, beta2=0.85):
    state = state or {}
    new_state={}; all_scores=[]
    for m in matrices:
        mid=m['id']; prev=state.get(mid,{})
        sens={k: abs_mul(m[k], m[k+'_grad']) for k in ['A','E','B']}
        avg={}; unc={}; score={}
        for k in ['A','E','B']:
            avg[k]=ewma(prev.get('avg',{}).get(k), sens[k], beta1)
            unc[k]=ewma(prev.get('unc',{}).get(k), sub_abs(sens[k], avg[k]), beta2)
            score[k]=elem_mul(avg[k], unc[k])
        trip=[]
        for i in range(len(m['E'])):
            s=score['E'][i] + row_mean(score['A'][i]) + col_mean(score['B'], i)
            trip.append(s); all_scores.append((s, mid, i))
        new_state[mid]={'avg':avg,'unc':unc,'triplet_scores':trip}
    return new_state, all_scores

def allocate(matrices, target_rank, state=None, beta1=0.85, beta2=0.85):
    new_state, all_scores=update_scores(matrices,state,beta1,beta2)
    target_rank=max(0,min(target_rank,len(all_scores)))
    ordered=sorted(enumerate(all_scores), key=lambda x: (-x[1][0], x[0]))
    keep={(mid,i) for _,(_,mid,i) in ordered[:target_rank]}
    threshold=ordered[target_rank-1][1][0] if target_rank else None
    out=[]; rank_pattern={}
    for m in matrices:
        masked=[]
        for i,v in enumerate(m['E']): masked.append(v if (m['id'],i) in keep else 0.0)
        rank_pattern[m['id']]=sum(1 for v in masked if abs(v)>1e-12)
        mm=dict(m); mm['E_masked']=masked; out.append(mm)
    return {'state':new_state,'scores':all_scores,'threshold':threshold,'matrices':out,'rank_pattern':rank_pattern,'target_rank':target_rank}

def self_test():
    mats=[{'id':'m1','A':[[1,0],[0.1,0]],'E':[1,1],'B':[[1,0.1],[0,0]],'A_grad':[[10,0],[0.1,0]],'E_grad':[10,0.1],'B_grad':[[10,0.1],[0,0]]}]
    res=allocate(mats,1,beta1=0.5,beta2=0.5)
    assert res['matrices'][0]['E_masked'][0]==1 and res['matrices'][0]['E_masked'][1]==0
    assert res['rank_pattern']['m1']==1
    return True

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--self-test', action='store_true'); ns=ap.parse_args()
    if ns.self_test: print(json.dumps({'ok':self_test()})); return
    d=json.load(open(ns.input)); print(json.dumps(allocate(**d), indent=2))
if __name__=='__main__': main()
