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

def init_lora(d_out,d_in,r):
    if r<=0 or r>min(d_out,d_in): raise ValueError('invalid rank')
    A=[[0.01*(i+1)*(j+1) for j in range(d_in)] for i in range(r)]
    B=zeros(d_out,r)
    return A,B

def forward(W0,A,B,x,alpha=1.0):
    base=mat_vec(W0,x); bax=mat_vec(B, mat_vec(A,x)); s=alpha/len(A)
    return [base[i]+s*bax[i] for i in range(len(base))]

def train(W0, examples, r=1, alpha=1.0, lr=0.1, steps=20):
    A,B=init_lora(len(W0),len(W0[0]),r); W_before=[row[:] for row in W0]
    params_before={'A':[row[:] for row in A],'B':[row[:] for row in B]}
    def loss(): return sum(sum((forward(W0,A,B,x,alpha)[i]-y[i])**2 for i in range(len(y))) for x,y in examples)/len(examples)
    loss_before=loss()
    for _ in range(steps):
        gA=zeros(r,len(W0[0])); gB=zeros(len(W0),r); s=alpha/r
        for x,y in examples:
            Ax=mat_vec(A,x); pred=forward(W0,A,B,x,alpha); err=[2*(pred[i]-y[i])/len(examples) for i in range(len(y))]
            for i in range(len(W0)):
                for k in range(r): gB[i][k]+=s*err[i]*Ax[k]
            Bt_err=[sum(B[i][k]*err[i] for i in range(len(W0))) for k in range(r)]
            for k in range(r):
                for j in range(len(x)): gA[k][j]+=s*Bt_err[k]*x[j]
        for i in range(len(B)):
            for k in range(r): B[i][k]-=lr*gB[i][k]
        for k in range(r):
            for j in range(len(A[0])): A[k][j]-=lr*gA[k][j]
    return {'loss_before':loss_before,'loss_after':loss(),'params_before':params_before,'params_after':{'A':A,'B':B},'W0_unchanged':W0==W_before}
