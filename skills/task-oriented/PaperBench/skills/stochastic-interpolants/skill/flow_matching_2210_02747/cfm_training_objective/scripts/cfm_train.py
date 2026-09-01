#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def make_features(t,x): return [1.0,t,t*t]+list(x)+[v*v for v in x]+[t*v for v in x]
def predict(params,t,x):
    f=make_features(t,x); return [sum(w*v for w,v in zip(row,f)) for row in params]
def mse_loss(params,times,x_t,targets):
    total=count=0
    for t,x,y in zip(times,x_t,targets):
        for p,yy in zip(predict(params,t,x),y): total+=(p-yy)**2; count+=1
    return total/max(count,1)
def gradient(params,times,x_t,targets):
    grad=[[0.0 for _ in row] for row in params]; count=sum(len(r) for r in targets)
    for t,x,y in zip(times,x_t,targets):
        f=make_features(t,x); pred=predict(params,t,x)
        for i,(p,yy) in enumerate(zip(pred,y)):
            scale=2*(p-yy)/max(count,1)
            for j,val in enumerate(f): grad[i][j]+=scale*val
    return grad
def train_linear_cfm(times,x_t,targets,steps=120,lr=.05,init_scale=0.0):
    dim=len(x_t[0]); feat=len(make_features(times[0],x_t[0])); params=[[init_scale*(i+1)*(j+1) for j in range(feat)] for i in range(dim)]; before=[r[:] for r in params]; loss0=mse_loss(params,times,x_t,targets); losses=[loss0]
    for _ in range(steps):
        g=gradient(params,times,x_t,targets)
        for i,row in enumerate(params):
            for j in range(len(row)): row[j]-=lr*g[i][j]
        losses.append(mse_loss(params,times,x_t,targets))
    loss1=losses[-1]
    return {'loss_before':loss0,'loss_after':loss1,'relative_loss_decrease':(loss0-loss1)/loss0 if loss0 else 0.0,'params_before':before,'params_after':params,'optimizer_step_executed':before!=params and steps>0,'losses':losses,'steps':steps,'lr':lr}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--path-json',required=True); p.add_argument('--steps',type=int,default=120); p.add_argument('--lr',type=float,default=.05); p.add_argument('--output',required=True); a=p.parse_args(); d=json.loads(Path(a.path_json).read_text()); tr=train_linear_cfm(d['t'],d['x_t'],d['u_t'],a.steps,a.lr); Path(a.output).write_text(json.dumps(tr,indent=2)); print(json.dumps({'loss_before':tr['loss_before'],'loss_after':tr['loss_after']},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
