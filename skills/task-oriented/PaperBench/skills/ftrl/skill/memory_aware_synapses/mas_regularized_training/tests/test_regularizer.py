import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from mas_train import train_linear_regression
start=[1.0,1.0]; feats=[[1,1],[1,-1]]; targets=[-1,-1]
f=train_linear_regression(start, targets, feats, lam=0, lr=0.1, steps=15)
m=train_linear_regression(start, targets, feats, theta_star=start, omega=[20,0], lam=1, lr=0.02, steps=15)
assert f['optimizer_step_executed'] and m['optimizer_step_executed']
assert abs(m['params_after'][0]-start[0]) < abs(f['params_after'][0]-start[0])
assert 'mas_penalty' in m['trace'][0]
