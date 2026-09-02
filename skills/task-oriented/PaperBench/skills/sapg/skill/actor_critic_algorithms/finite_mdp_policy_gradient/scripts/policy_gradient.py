from __future__ import annotations
import math

def softmax(logits):
    m=max(logits); ex=[math.exp(x-m) for x in logits]; z=sum(ex); return [v/z for v in ex]

def build_policy(theta, features):
    return [[p for p in softmax([sum(t*f for t,f in zip(theta, features[s][a])) for a in range(len(features[s]))])] for s in range(len(features))]

def solve_linear(matrix, rhs):
    n=len(rhs); a=[row[:] + [rhs[i]] for i,row in enumerate(matrix)]
    for col in range(n):
        piv=max(range(col,n), key=lambda r: abs(a[r][col])); a[col],a[piv]=a[piv],a[col]
        if abs(a[col][col]) < 1e-12: raise ValueError('singular system')
        div=a[col][col]; a[col]=[x/div for x in a[col]]
        for r in range(n):
            if r==col: continue
            fac=a[r][col]; a[r]=[x-fac*y for x,y in zip(a[r],a[col])]
    return [a[i][-1] for i in range(n)]

def evaluate_mdp(transitions, rewards, gamma, start, policy):
    n=len(policy); A=len(policy[0])
    rpi=[sum(policy[s][a]*rewards[s][a] for a in range(A)) for s in range(n)]
    ppi=[[sum(policy[s][a]*transitions[s][a][sp] for a in range(A)) for sp in range(n)] for s in range(n)]
    mat=[[float(i==j)-gamma*ppi[i][j] for j in range(n)] for i in range(n)]
    v=solve_linear(mat, rpi)
    q=[[rewards[s][a]+gamma*sum(transitions[s][a][sp]*v[sp] for sp in range(n)) for a in range(A)] for s in range(n)]
    objective=sum(start[s]*v[s] for s in range(n))
    occ=solve_linear([[float(i==j)-gamma*sum(ppi[sp][i] for sp in range(n)) for j in range(n)] for i in range(n)], start) if False else discounted_occupancy(ppi,gamma,start)
    return {'v':v,'q':q,'objective':objective,'occupancy':occ,'policy':policy}

def discounted_occupancy(ppi,gamma,start):
    n=len(start)
    # Solve d = start + gamma P_pi^T d
    mat=[[float(i==j)-gamma*ppi[j][i] for j in range(n)] for i in range(n)]
    return solve_linear(mat, start[:])

def score_features(policy, features):
    n=len(policy); A=len(policy[0]); d=len(features[0][0]); out=[]
    for s in range(n):
        mean=[sum(policy[s][b]*features[s][b][k] for b in range(A)) for k in range(d)]
        out.append([[features[s][a][k]-mean[k] for k in range(d)] for a in range(A)])
    return out

def theorem_gradient(theta, transitions, rewards, gamma, start, features):
    policy=build_policy(theta, features); ev=evaluate_mdp(transitions,rewards,gamma,start,policy); scores=score_features(policy,features)
    d=len(theta); grad=[0.0]*d
    for s,ds in enumerate(ev['occupancy']):
        for a,pa in enumerate(policy[s]):
            for k in range(d): grad[k]+=ds*pa*scores[s][a][k]*ev['q'][s][a]
    return grad, ev, scores

def finite_difference_gradient(theta, transitions, rewards, gamma, start, features, eps=1e-6):
    grad=[]
    for k in range(len(theta)):
        plus=theta[:]; minus=theta[:]; plus[k]+=eps; minus[k]-=eps
        fp=evaluate_mdp(transitions,rewards,gamma,start,build_policy(plus,features))['objective']
        fm=evaluate_mdp(transitions,rewards,gamma,start,build_policy(minus,features))['objective']
        grad.append((fp-fm)/(2*eps))
    return grad

def gradient_error(a,b): return max(abs(x-y) for x,y in zip(a,b))

def demo_mdp():
    transitions=[[[0.8,0.2],[0.1,0.9]],[[0.6,0.4],[0.0,1.0]]]
    rewards=[[0.2,1.0],[0.5,0.1]]; gamma=0.85; start=[1.0,0.0]
    features=[[[1.0,0.0],[0.0,1.0]],[[0.5,1.0],[1.0,-0.5]]]
    theta=[0.15,-0.2]
    return transitions,rewards,gamma,start,features,theta
