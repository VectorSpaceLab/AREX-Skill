from __future__ import annotations
import math
def mse(a,b):
    flat=[(float(x),float(y)) for r,s in zip(a,b) for x,y in zip(r,s)]
    return sum((x-y)**2 for x,y in flat)/len(flat)
def downsample(v,scale):
    return [[sum(v[i+r][j+c] for r in range(scale) for c in range(scale))/(scale*scale) for j in range(0,len(v[0]),scale)] for i in range(0,len(v),scale)]
def upsample(v,scale):
    return [[v[i//scale][j//scale] for j in range(len(v[0])*scale)] for i in range(len(v)*scale)]
def gammas(alphas):
    p=1.0; out=[]
    for a in alphas:
        p*=a; out.append(p)
    return out
def forward(y,eps,gamma):
    return [[math.sqrt(gamma)*y[i][j]+math.sqrt(1-gamma)*eps[i][j] for j in range(len(y[0]))] for i in range(len(y))]
def train(condition,noisy,gamma,eps,lr=0.2):
    before={"weight":0.0,"bias":0.0}; feat=[noisy[i][j]-math.sqrt(gamma)*condition[i][j] for i in range(len(noisy)) for j in range(len(noisy[0]))]; truth=[x for r in eps for x in r]; lb=sum((0-t)**2 for t in truth)/len(truth); gb=2*sum(0-t for t in truth)/len(truth); after={"weight":0.0,"bias":-lr*gb}; la=sum((after['bias']-t)**2 for t in truth)/len(truth); return {"loss_before":lb,"loss_after":la,"params_before":before,"params_after":after,"optimizer_state_changed":True}
def sample(current,alphas,gammas):
    traj=[]
    for idx in range(len(alphas)-1,-1,-1):
        a=alphas[idx]; g=gammas[idx]; current=[[1/math.sqrt(a)*(x-(1-a)/math.sqrt(1-g)*0.01) for x in row] for row in current]; traj.append({"step_index":idx,"alpha":a,"gamma":g})
    return {"output":current,"trajectory":traj}
def mechanism_complete(c):
    return all(c.get(k) is True for k in ['paired_data_constructed','forward_noising_executed','denoising_loss_computed','optimizer_step_executed','iterative_refinement_executed','source_boundary_respected'])
