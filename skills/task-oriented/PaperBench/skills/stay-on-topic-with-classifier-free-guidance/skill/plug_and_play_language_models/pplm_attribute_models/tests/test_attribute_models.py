import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from attribute_models import bow_loss

def test_bow_loss_prefers_target_mass():
    loss1,d1=bow_loss([0.8,0.1,0.1], ['science','dog','cat'], ['science'])
    loss2,d2=bow_loss([0.1,0.8,0.1], ['science','dog','cat'], ['science'])
    assert loss1 < loss2
    assert d1['matched_terms']==['science']

def test_unknown_words_report_empty_match():
    loss,d=bow_loss([0.5,0.5], ['a','b'], ['missing'])
    assert d['matched_terms']==[]
    assert d['target_mass']==0
