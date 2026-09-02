import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from candidate_reranking import select_candidate, distinct_n

def test_distinct_n_and_diversity_filter():
    assert distinct_n(['a','b','a'],1)==2/3
    best,rows=select_candidate([{'tokens':['x','x','x'],'attribute_score':9},{'tokens':['a','b','c'],'attribute_score':5}], min_dist1=0.8)
    assert best['tokens']==['a','b','c']

def test_fallback_when_all_fail_diversity():
    best,rows=select_candidate([{'tokens':['x','x','x'],'attribute_score':9},{'tokens':['a','a','a'],'attribute_score':5}], min_dist1=0.8)
    assert best['attribute_score']==9
    assert best['selection_reason']=='fallback_all_failed_diversity'
