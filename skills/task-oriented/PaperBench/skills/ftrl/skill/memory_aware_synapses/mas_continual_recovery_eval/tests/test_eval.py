import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from evaluate_forgetting import summarize_recovery
s=summarize_recovery(.95,.55,.80)
assert s['forgetting_reduction'] > 0 and s['mas_reduces_forgetting'] is True
