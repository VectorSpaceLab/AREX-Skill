import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from mas_importance import estimate_linear_importance
r=estimate_linear_importance([2.0,0.5], [[1,0],[2,0]])
assert r['importance'][0] > r['importance'][1] and r['labels_used'] is False
try:
    estimate_linear_importance([1.0], [])
    raise AssertionError('empty samples should fail')
except ValueError: pass
