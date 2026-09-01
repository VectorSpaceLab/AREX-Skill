#!/usr/bin/env python3
from __future__ import annotations
import argparse, json

def _is_vector(value): return isinstance(value, list) and all(isinstance(v, (int, float)) for v in value)
def _is_matrix(value): return isinstance(value, list) and value and all(_is_vector(row) for row in value)
def as_batch(value):
    if _is_vector(value): return [list(map(float, value))]
    if _is_matrix(value):
        width=len(value[0])
        if any(len(row)!=width for row in value): raise ValueError('ragged vectors are not supported')
        return [list(map(float,row)) for row in value]
    raise ValueError('expected a vector or non-empty batch of vectors')
def broadcast_times(t, batch_size):
    times=[float(t)]*batch_size if isinstance(t,(int,float)) else [float(v) for v in t] if isinstance(t,list) and len(t)==batch_size else None
    if times is None: raise ValueError('time must be a scalar or match batch size')
    if any(v<0.0 or v>1.0 for v in times): raise ValueError('time values must be in [0, 1]')
    return times
def ot_conditional_path(x0, x1, t, sigma_min=0.001):
    if sigma_min<0.0 or sigma_min>1.0: raise ValueError('sigma_min must be in [0, 1]')
    b0,b1=as_batch(x0),as_batch(x1)
    if len(b0)!=len(b1) or any(len(a)!=len(b) for a,b in zip(b0,b1)): raise ValueError('x0 and x1 must have matching shapes')
    times=broadcast_times(t,len(b0)); xt=[]; ut=[]; sig=[]
    for noise,data,time_value in zip(b0,b1,times):
        sigma_t=1.0-(1.0-sigma_min)*time_value; sig.append(sigma_t)
        xt.append([sigma_t*a+time_value*b for a,b in zip(noise,data)])
        ut.append([b-(1.0-sigma_min)*a for a,b in zip(noise,data)])
    return {'path_type':'ot','sigma_min':sigma_min,'t':times,'sigma_t':sig,'x_t':xt,'u_t':ut,'target_formula':'u_t = x1 - (1 - sigma_min) * x0'}
def finite_difference_velocity(x0,x1,t,sigma_min=0.001,eps=1e-6):
    before=ot_conditional_path(x0,x1,max(0.0,t-eps),sigma_min)['x_t']; after=ot_conditional_path(x0,x1,min(1.0,t+eps),sigma_min)['x_t']; denom=min(1.0,t+eps)-max(0.0,t-eps)
    return [[(b-a)/denom for a,b in zip(rb,ra)] for rb,ra in zip(before,after)]
def main():
    p=argparse.ArgumentParser(); p.add_argument('--x0',required=True); p.add_argument('--x1',required=True); p.add_argument('--t',required=True); p.add_argument('--sigma-min',type=float,default=0.001); a=p.parse_args()
    print(json.dumps(ot_conditional_path(json.loads(a.x0),json.loads(a.x1),json.loads(a.t),a.sigma_min),indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
