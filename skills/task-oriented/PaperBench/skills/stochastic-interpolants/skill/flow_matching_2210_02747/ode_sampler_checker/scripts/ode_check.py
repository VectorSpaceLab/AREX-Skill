#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path

def euler_constant_velocity(x0,velocity,steps=10):
    if steps<=0: raise ValueError('steps must be positive')
    if len(x0)!=len(velocity): raise ValueError('x0 and velocity must have matching dimensions')
    state=[float(v) for v in x0]; traj=[state[:]]; dt=1.0/steps
    for _ in range(steps): state=[a+dt*b for a,b in zip(state,velocity)]; traj.append(state[:])
    return {'trajectory':traj,'final':state,'nfe':steps,'solver':'euler','steps':steps}
def endpoint_error(final,target):
    if len(final)!=len(target): raise ValueError('final and target must have matching dimensions')
    return math.sqrt(sum((a-b)**2 for a,b in zip(final,target)))
def main():
    p=argparse.ArgumentParser(); p.add_argument('--x0',required=True); p.add_argument('--velocity',required=True); p.add_argument('--target',default=''); p.add_argument('--steps',type=int,default=10); p.add_argument('--output',required=True); a=p.parse_args(); r=euler_constant_velocity(json.loads(a.x0),json.loads(a.velocity),a.steps)
    if a.target: r['target']=json.loads(a.target); r['endpoint_error']=endpoint_error(r['final'],r['target'])
    Path(a.output).write_text(json.dumps(r,indent=2)); print(json.dumps({'nfe':r['nfe'],'final':r['final'],'endpoint_error':r.get('endpoint_error')},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
