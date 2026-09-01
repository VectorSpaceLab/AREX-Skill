from math import isfinite

def mat_vec(M, x):
    return [sum(row[j]*x[j] for j in range(len(x))) for row in M]

def outer(u, v):
    return [[ui*vj for vj in v] for ui in u]

def zeros(n,m): return [[0.0 for _ in range(m)] for __ in range(n)]

def add(A,B): return [[A[i][j]+B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def scale(A,s): return [[s*v for v in row] for row in A]

def matmul(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]

def merged_weight(W0,A,B,alpha=1.0):
    return add(W0, scale(matmul(B,A), alpha/len(A)))

def forward_merged(W0,A,B,x,alpha=1.0):
    return mat_vec(merged_weight(W0,A,B,alpha), x)

def equivalence_error(forward_func,W0,A,B,inputs,alpha=1.0):
    errs=[]
    for x in inputs:
        y1=forward_func(W0,A,B,x,alpha); y2=forward_merged(W0,A,B,x,alpha)
        errs += [abs(a-b) for a,b in zip(y1,y2)]
    return max(errs) if errs else 0.0
