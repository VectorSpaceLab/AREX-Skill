import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from adapt_importance import accumulate_importance
try:
    accumulate_importance([1.0], [1.0, 2.0])
    raise AssertionError('misaligned importance vectors must fail')
except ValueError as exc:
    assert 'align' in str(exc)
