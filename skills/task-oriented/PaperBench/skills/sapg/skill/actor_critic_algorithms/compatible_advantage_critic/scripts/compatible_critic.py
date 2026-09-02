from __future__ import annotations

def solve_linear(matrix, rhs):
    n=len(rhs); a=[row[:] + [rhs[i]] for i,row in enumerate(matrix)]
    for col in range(n):
        piv=max(range(col,n), key=lambda r: abs(a[r][col])); a[col],a[piv]=a[piv],a[col]
        if abs(a[col][col]) < 1e-12: a[col][col]=1e-12
        div=a[col][col]; a[col]=[x/div for x in a[col]]
        for r in range(n):
            if r==col: continue
            fac=a[r][col]; a[r]=[x-fac*y for x,y in zip(a[r],a[col])]
    return [a[i][-1] for i in range(n)]

def fit_compatible_critic(policy, q_values, occupancy, score_features):
    d=len(score_features[0][0]); xtwx=[[0.0]*d for _ in range(d)]; xtwy=[0.0]*d
    for s,ds in enumerate(occupancy):
        for a,pa in enumerate(policy[s]):
            w=ds*pa; x=score_features[s][a]; y=q_values[s][a]
            for i in range(d):
                xtwy[i]+=w*x[i]*y
                for j in range(d): xtwx[i][j]+=w*x[i]*x[j]
    weights=solve_linear(xtwx, xtwy)
    pred=[[sum(weights[k]*score_features[s][a][k] for k in range(d)) for a in range(len(policy[s]))] for s in range(len(policy))]
    residual=[0.0]*d
    for s,ds in enumerate(occupancy):
        for a,pa in enumerate(policy[s]):
            err=q_values[s][a]-pred[s][a]
            for k in range(d): residual[k]+=ds*pa*err*score_features[s][a][k]
    grad=[0.0]*d
    for s,ds in enumerate(occupancy):
        for a,pa in enumerate(policy[s]):
            for k in range(d): grad[k]+=ds*pa*score_features[s][a][k]*pred[s][a]
    return {'weights':weights,'predictions':pred,'orthogonality_residual':residual,'critic_gradient':grad,'orthogonality_norm':max(abs(x) for x in residual)}
