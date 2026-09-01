import math

def _matvec(A, x):
    return [sum(float(a)*float(v) for a,v in zip(row,x)) for row in A]

def _sqnorm(v):
    return sum(float(x)*float(x) for x in v)

def _solve(M, y):
    n=len(y); A=[list(map(float,row))+[float(y[i])] for i,row in enumerate(M)]
    for c in range(n):
        piv=max(range(c,n), key=lambda r: abs(A[r][c]))
        if abs(A[piv][c]) < 1e-12: raise ValueError('singular system')
        A[c],A[piv]=A[piv],A[c]
        div=A[c][c]; A[c]=[v/div for v in A[c]]
        for r in range(n):
            if r==c: continue
            fac=A[r][c]
            A[r]=[rv-fac*cv for rv,cv in zip(A[r],A[c])]
    return [A[i][-1] for i in range(n)]

def tune(A, b, keep_mask, damp=1.0, value_range=(-10.0,10.0)):
    A=[list(map(float,row)) for row in A]; b=list(map(float,b)); cols=len(keep_mask)
    keep=[i for i,v in enumerate(keep_mask) if int(v)==1]
    base=[float(int(v)) for v in keep_mask]
    baseline=_sqnorm([u-v for u,v in zip(_matvec(A,base),b)])
    if not keep:
        return {'mask':base,'baseline_error':baseline,'tuned_error':baseline,'accepted':True,'skipped':True}
    # damped normal equations on kept columns
    k=len(keep); M=[[0.0]*k for _ in range(k)]; y=[0.0]*k
    for row, target in zip(A,b):
        ar=[row[i] for i in keep]
        for i in range(k):
            y[i]+=ar[i]*target
            for j in range(k): M[i][j]+=ar[i]*ar[j]
    for i in range(k): M[i][i]+=float(damp)**2
    coef=_solve(M,y)
    lo,hi=value_range
    full=[0.0]*cols
    for idx,c in zip(keep,coef): full[idx]=c
    accepted=all(c>=lo and c<=hi for c in coef)
    if not accepted:
        return {'mask':base,'baseline_error':baseline,'tuned_error':baseline,'accepted':False,'reason':'range_guard'}
    tuned=_sqnorm([u-v for u,v in zip(_matvec(A,full),b)])
    return {'mask':full,'baseline_error':baseline,'tuned_error':tuned,'accepted':True,'skipped':False}
