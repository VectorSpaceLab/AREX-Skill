#!/usr/bin/env python3
"""Tiny PaddedGraphGenerator smoke for StellarGraph graph classification."""
from __future__ import print_function
import argparse, sys
from pathlib import Path

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--repo-root'); a=p.parse_args(argv)
    if a.repo_root: sys.path.insert(0, str(Path(a.repo_root).expanduser().resolve()))
    import numpy as np, pandas as pd
    from stellargraph import StellarGraph
    from stellargraph.mapper import PaddedGraphGenerator
    g1=StellarGraph(pd.DataFrame({'x':[1.0,0.0]}, index=['a','b']), pd.DataFrame({'source':['a'], 'target':['b']}))
    g2=StellarGraph(pd.DataFrame({'x':[0.5,0.2,0.1]}, index=['c','d','e']), pd.DataFrame({'source':['c','d'], 'target':['d','e']}))
    gen=PaddedGraphGenerator([g1,g2])
    seq=gen.flow([0,1], np.array([[1.0,0.0],[0.0,1.0]]), batch_size=2)
    x,y=seq[0]
    print('input_shapes:', [getattr(v,'shape',None) for v in x], 'target_shape:', getattr(y,'shape',None))
    print('graph batch smoke: ok')
    return 0
if __name__=='__main__': raise SystemExit(main())
