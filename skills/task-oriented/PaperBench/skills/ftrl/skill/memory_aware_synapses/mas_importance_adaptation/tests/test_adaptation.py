import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from adapt_importance import accumulate_importance, subset_concentration
assert accumulate_importance([1,0],[2,.5])['importance']==[3,.5]
assert subset_concentration([3,.5],[0],[1])['concentration_ratio'] > 5
