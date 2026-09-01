#!/usr/bin/env python3
import argparse, json

def schedule(step,total_step,initial_warmup,final_warmup,initial_rank,target_rank,mask_interval):
    if total_step <= initial_warmup + final_warmup: raise ValueError('total_step must exceed warmups')
    if target_rank > initial_rank: raise ValueError('target_rank cannot exceed initial_rank')
    if mask_interval <= 0: raise ValueError('mask_interval must be positive')
    if step <= initial_warmup:
        return {'rank': int(initial_rank), 'mask': False, 'phase': 'initial_warmup'}
    if step > total_step - final_warmup:
        return {'rank': int(target_rank), 'mask': True, 'phase': 'final_warmup'}
    progress=(step-initial_warmup)/(total_step-final_warmup-initial_warmup)
    rank=int(target_rank+(initial_rank-target_rank)*((1-progress)**3))
    return {'rank': rank, 'mask': step % mask_interval == 0, 'phase': 'decay'}

def self_test():
    assert schedule(1,10,2,2,8,4,2)['rank']==8
    mid=schedule(4,10,2,2,8,4,2); assert mid['mask'] is True and 4 <= mid['rank'] <= 8
    assert schedule(9,10,2,2,8,4,2)=={'rank':4,'mask':True,'phase':'final_warmup'}
    return True

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test', action='store_true'); ap.add_argument('--input')
    ns=ap.parse_args()
    if ns.self_test: print(json.dumps({'ok':self_test()})); return
    d=json.load(open(ns.input)); print(json.dumps(schedule(**d), indent=2))
if __name__=='__main__': main()
