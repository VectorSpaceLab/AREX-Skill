#!/usr/bin/env python3
"""Tiny SlidingFeaturesNodeGenerator smoke for StellarGraph time-series workflows."""
from __future__ import print_function
import argparse, sys
from pathlib import Path

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--repo-root'); a=p.parse_args(argv)
    if a.repo_root: sys.path.insert(0, str(Path(a.repo_root).expanduser().resolve()))
    import numpy as np, pandas as pd
    from stellargraph import StellarGraph
    from stellargraph.mapper import SlidingFeaturesNodeGenerator
    # feature rows are nodes; columns are time points for this generator path
    nodes=pd.DataFrame(np.arange(12,dtype='float32').reshape(3,4), index=['a','b','c'])
    edges=pd.DataFrame({'source':['a','b'], 'target':['b','c']})
    graph=StellarGraph(nodes, edges)
    gen=SlidingFeaturesNodeGenerator(graph, window_size=2, batch_size=1)
    seq=gen.flow(slice(0,4), target_distance=1)
    x,y=seq[0]
    print('input_shape:', getattr(x,'shape',None), 'target_shape:', getattr(y,'shape',None))
    print('time series shape smoke: ok')
    return 0
if __name__=='__main__': raise SystemExit(main())
