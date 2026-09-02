#!/usr/bin/env python3
import argparse, itertools, json, math
from pathlib import Path

def norm(vec): return math.sqrt(sum(v*v for v in vec))
def aggregate(vectors, indices):
    dim=len(vectors[0]); out=[0.0]*dim
    for idx in indices:
        for j in range(dim): out[j]+=vectors[idx][j]
    return out

def validate(vectors):
    if not vectors: raise ValueError('no influence vectors')
    dim=len(vectors[0])
    for vec in vectors:
        if len(vec)!=dim: raise ValueError('influence dimension mismatch')
        if not all(math.isfinite(v) for v in vec): raise ValueError('non-finite influence')

def select_subset(vectors, epsilon=None, cardinality=None):
    validate(vectors); n=len(vectors)
    best=None
    if cardinality is not None:
        candidates=itertools.combinations(range(n), int(cardinality))
    else:
        candidates=(combo for r in range(n+1) for combo in itertools.combinations(range(n), r))
    for combo in candidates:
        agg=aggregate(vectors, combo); value=norm(agg)
        feasible=True if epsilon is None else value <= epsilon + 1e-12
        if not feasible: continue
        key=(len(combo), -value)
        if best is None or key > best[0]: best=(key, combo, agg, value)
    if best is None: best=((0, -0.0), tuple(), [0.0]*len(vectors[0]), 0.0)
    indices=list(best[1]); mask=[i in indices for i in range(n)]
    return {'schema_version':1,'selected_indices':indices,'selected_mask':mask,'aggregate_influence':best[2],'aggregate_norm':best[3],'selected_count':len(indices),'epsilon':epsilon,'feasible':epsilon is None or best[3] <= epsilon + 1e-12,'search':'exhaustive'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--output'); p.add_argument('--epsilon', type=float); p.add_argument('--cardinality', type=int); p.add_argument('--demo', action='store_true')
    a=p.parse_args(); data={'influences':[[1,0],[-1,0],[0,0.4],[0,0.4]],'epsilon':0.45} if a.demo else json.loads(Path(a.input).read_text())
    out=select_subset(data.get('influences'), a.epsilon if a.epsilon is not None else data.get('epsilon'), a.cardinality if a.cardinality is not None else data.get('cardinality'))
    text=json.dumps(out, indent=2)
    if a.output: Path(a.output).write_text(text+'\n')
    else: print(text)
if __name__=='__main__': main()
