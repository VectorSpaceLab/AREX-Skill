#!/usr/bin/env python3
import json, argparse, math

def matvec(matrix, vector):
    return [sum(row[i] * vector[i] for i in range(len(vector))) for row in matrix]

def transpose(matrix):
    return [list(row) for row in zip(*matrix)]

def matmul(left, right):
    right_t = transpose(right)
    return [[sum(a*b for a,b in zip(row,col)) for col in right_t] for row in left]

def add_matrix(a, b):
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]

def scale_matrix(a, scale):
    return [[scale * v for v in row] for row in a]

def lora_delta(a_matrix, b_matrix, alpha):
    rank = len(a_matrix)
    if rank == 0:
        return []
    return scale_matrix(matmul(b_matrix, a_matrix), alpha / rank)

def lora_forward(weight, a_matrix, b_matrix, alpha, vector):
    base = matvec(weight, vector)
    if not a_matrix:
        return base
    delta = matvec(lora_delta(a_matrix, b_matrix, alpha), vector)
    return [base[i] + delta[i] for i in range(len(base))]

def merge_weight(weight, a_matrix, b_matrix, alpha):
    if not a_matrix:
        return [row[:] for row in weight]
    return add_matrix(weight, lora_delta(a_matrix, b_matrix, alpha))

def count_trainable(in_features, out_features, rank):
    return rank * (in_features + out_features)

def max_abs_diff(a, b):
    return max(abs(x-y) for x,y in zip(a,b)) if a else 0.0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ns=ap.parse_args()
    data=json.load(open(ns.input))
    y=lora_forward(data['weight'], data['A'], data['B'], data.get('alpha',1.0), data['x'])
    merged=merge_weight(data['weight'], data['A'], data['B'], data.get('alpha',1.0))
    y2=matvec(merged, data['x'])
    print(json.dumps({'prediction':y,'merged_prediction':y2,'merge_max_abs_diff':max_abs_diff(y,y2),'trainable_parameters':count_trainable(len(data['weight'][0]),len(data['weight']),len(data['A']))}, indent=2))
if __name__ == '__main__': main()
