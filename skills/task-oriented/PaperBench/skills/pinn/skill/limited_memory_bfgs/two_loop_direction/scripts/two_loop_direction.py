from __future__ import annotations
from typing import Iterable, List, Sequence, Tuple
Vector = List[float]
Pair = Tuple[Vector, Vector]

def dot(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b): raise ValueError("vectors must have matching dimensions")
    return sum(x*y for x,y in zip(a,b))

def axpy(a: float, x: Sequence[float], y: Sequence[float]) -> Vector:
    if len(x) != len(y): raise ValueError("vectors must have matching dimensions")
    return [a*xi+yi for xi,yi in zip(x,y)]

def newest_scale(memory: Sequence[Pair]) -> float:
    if not memory: return 1.0
    s,y=memory[-1]; yy=dot(y,y)
    return dot(s,y)/yy if yy > 0 else 1.0

def lbfgs_direction(gradient: Sequence[float], memory: Iterable[Pair], scaling: float | None = None):
    pairs=[(list(s), list(y)) for s,y in memory if dot(s,y) > 1e-12]
    q=list(gradient); alphas=[]; rhos=[]
    for s,y in reversed(pairs):
        rho=1.0/dot(s,y); alpha=rho*dot(s,q); q=axpy(-alpha,y,q)
        alphas.append(alpha); rhos.append(rho)
    scale = newest_scale(pairs) if scaling is None else scaling
    r=[scale*qi for qi in q]
    for (s,y), alpha, rho in zip(pairs, reversed(alphas), reversed(rhos)):
        beta=rho*dot(y,r); r=axpy(alpha-beta,s,r)
    direction=[-ri for ri in r]
    return {"direction": direction, "pair_count": len(pairs), "scaling": scale, "descent_dot": dot(direction, gradient)}
