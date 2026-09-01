#!/usr/bin/env python3
import json, argparse
from pathlib import Path
try:
    from lora_math import lora_forward, merge_weight, matvec
except ModuleNotFoundError:
    def matvec(matrix, vector):
        return [sum(row[i] * vector[i] for i in range(len(vector))) for row in matrix]

    def transpose(matrix):
        return [list(row) for row in zip(*matrix)]

    def matmul(left, right):
        right_t = transpose(right)
        return [[sum(a * b for a, b in zip(row, col)) for col in right_t] for row in left]

    def lora_delta(a_matrix, b_matrix, alpha):
        rank = len(a_matrix)
        scale = alpha / rank
        return [[scale * v for v in row] for row in matmul(b_matrix, a_matrix)]

    def lora_forward(weight, a_matrix, b_matrix, alpha, vector):
        base = matvec(weight, vector)
        delta = matvec(lora_delta(a_matrix, b_matrix, alpha), vector)
        return [base[i] + delta[i] for i in range(len(base))]

    def merge_weight(weight, a_matrix, b_matrix, alpha):
        delta = lora_delta(a_matrix, b_matrix, alpha)
        return [[weight[i][j] + delta[i][j] for j in range(len(weight[0]))] for i in range(len(weight))]

def mse(weight,A,B,alpha,examples):
    total=0.0
    for x,y in examples:
        pred=lora_forward(weight,A,B,alpha,x)[0]
        total += (pred-y)**2
    return total/len(examples)

def step(weight,A,B,alpha,examples,lr=0.05):
    before=json.loads(json.dumps({'A':A,'B':B,'weight':weight}))
    rank=len(A); scale=alpha/rank
    grad_A=[[0.0 for _ in row] for row in A]
    grad_B=[[0.0 for _ in row] for row in B]
    for x,y in examples:
        pred=lora_forward(weight,A,B,alpha,x)[0]
        err=2*(pred-y)/len(examples)
        for q in range(rank):
            ax=sum(A[q][i]*x[i] for i in range(len(x)))
            grad_B[0][q] += err * scale * ax
            for i in range(len(x)):
                grad_A[q][i] += err * scale * B[0][q] * x[i]
    for q in range(rank):
        B[0][q] -= lr * grad_B[0][q]
        for i in range(len(A[q])):
            A[q][i] -= lr * grad_A[q][i]
    return before, {'A':A,'B':B,'weight':weight}

def run(examples=None, steps=8, lr=0.1):
    if examples is None:
        examples=[([1.0,0.0],1.2),([0.0,1.0],-0.7),([1.0,1.0],0.5),([2.0,-1.0],3.1)]
    weight=[[0.2,-0.1]]
    A=[[0.5,-0.25]]
    B=[[0.0]]
    alpha=2.0
    loss_before=mse(weight,A,B,alpha,examples)
    params_before={'A':[row[:] for row in A], 'B':[row[:] for row in B], 'weight':[row[:] for row in weight]}
    params_after={'A':[row[:] for row in A], 'B':[row[:] for row in B], 'weight':[row[:] for row in weight]}
    for _ in range(steps):
        _, params_after = step(weight,A,B,alpha,examples,lr)
    loss_after=mse(weight,A,B,alpha,examples)
    merged=merge_weight(weight,A,B,alpha)
    dyn=[lora_forward(weight,A,B,alpha,x)[0] for x,_ in examples]
    mrg=[matvec(merged,x)[0] for x,_ in examples]
    return {'loss_before':loss_before,'loss_after':loss_after,'params_before':params_before,'params_after':params_after,'optimizer_state_changed':params_before != params_after,'base_weight_unchanged':params_before['weight']==params_after['weight'],'merge_max_abs_diff':max(abs(a-b) for a,b in zip(dyn,mrg))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output', required=True); ap.add_argument('--steps', type=int, default=8); ap.add_argument('--lr', type=float, default=0.1)
    ns=ap.parse_args(); out=run(steps=ns.steps, lr=ns.lr)
    Path(ns.output).parent.mkdir(parents=True, exist_ok=True); Path(ns.output).write_text(json.dumps(out,indent=2))
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
