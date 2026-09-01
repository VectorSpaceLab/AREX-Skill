import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from rescore import fudge_rescore

def test_future_evidence_changes_probability_and_normalizes():
    base={'tea': 3.0, 'earth': 2.0, 'orbit': 1.0}
    fut={'tea': 0.05, 'earth': 0.95, 'orbit': 0.9}
    out=fudge_rescore(['mysterious'], base, fut, strength=2.0)
    assert abs(sum(out['probabilities'].values())-1.0) < 1e-9
    assert out['probabilities']['earth'] > out['probabilities']['tea']

def test_top_k_filtering():
    base={'tea': 3.0, 'earth': 2.0, 'orbit': 1.0}
    fut={'tea': 0.05, 'earth': 0.95, 'orbit': 0.9}
    out2=fudge_rescore([], base, fut, top_k=2)
    assert 'orbit' not in out2['probabilities']
