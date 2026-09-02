#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def mat_vec(matrix, vector):
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]

def solve_linear(matrix, vector):
    n=len(vector)
    aug=[list(map(float, matrix[i]))+[float(vector[i])] for i in range(n)]
    for col in range(n):
        pivot=max(range(col,n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError('singular damped curvature matrix')
        aug[col],aug[pivot]=aug[pivot],aug[col]
        scale=aug[col][col]
        aug[col]=[x/scale for x in aug[col]]
        for row in range(n):
            if row==col: continue
            factor=aug[row][col]
            aug[row]=[aug[row][k]-factor*aug[col][k] for k in range(n+1)]
    return [aug[i][-1] for i in range(n)]

def per_example_logistic_gradients(features, labels, params):
    gradients=[]
    for x,y in zip(features, labels):
        logit=sum(params[i]*x[i] for i in range(len(params)))
        prob=1.0/(1.0+math.exp(-logit))
        gradients.append([(prob-y)*xi for xi in x])
    return gradients

def empirical_curvature(features, damping=0.0):
    dim=len(features[0])
    mat=[[0.0]*dim for _ in range(dim)]
    for x in features:
        for i in range(dim):
            for j in range(dim):
                mat[i][j]+=x[i]*x[j]/len(features)
    for i in range(dim):
        mat[i][i]+=damping
    return mat

def estimate_influences(features=None, labels=None, params=None, gradients=None, curvature=None, damping=1e-2):
    if gradients is None:
        if features is None or labels is None or params is None:
            raise ValueError('features, labels, and params are required when gradients are absent')
        gradients=per_example_logistic_gradients(features, labels, params)
    dim=len(gradients[0])
    if curvature is None:
        if features is None:
            curvature=[[1.0 if i==j else 0.0 for j in range(dim)] for i in range(dim)]
        else:
            curvature=empirical_curvature(features, damping=0.0)
    damped=[row[:] for row in curvature]
    for i in range(dim): damped[i][i]+=damping
    n=len(gradients)
    influences=[]
    for grad in gradients:
        solved=solve_linear(damped, grad)
        influences.append([-(v/n) for v in solved])
    if not all(math.isfinite(v) for vec in influences for v in vec):
        raise ValueError('non-finite influence value')
    return {'schema_version':1,'influences':influences,'metadata':{'sample_count':n,'dimension':dim,'damping':damping,'sign_convention':'negative damped inverse curvature gradient divided by n','finite':True}}

def demo_payload():
    return {'features':[[1.0,0.0],[0.0,1.0],[1.0,1.0],[-1.0,0.5]],'labels':[1,0,1,0],'params':[0.2,-0.1],'damping':0.05}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--output'); p.add_argument('--demo', action='store_true')
    a=p.parse_args(); data=demo_payload() if a.demo else json.loads(Path(a.input).read_text())
    out=estimate_influences(**data)
    text=json.dumps(out, indent=2)
    if a.output: Path(a.output).write_text(text+'\n')
    else: print(text)
if __name__=='__main__': main()
