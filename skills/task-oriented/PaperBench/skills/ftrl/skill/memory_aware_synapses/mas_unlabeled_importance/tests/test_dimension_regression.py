import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from mas_importance import estimate_linear_importance
try:
    estimate_linear_importance([1.0, 2.0], [[1.0]])
    raise AssertionError('dimension mismatch must fail')
except ValueError as exc:
    assert 'dimension' in str(exc)
