from evaluate_selection_policies import build_extreme_policies, evaluate_policies

def test_moderate_advantage_positive_on_fixture():
    scores=[{'id':str(i),'label':i%2,'score':s} for i,s in enumerate([0,1,4,5,6,9,10])]
    policies=build_extreme_policies(scores,3)
    policies['moderate']=['2','3','4']
    out=evaluate_policies(scores,policies)
    assert out['moderate_selection_advantage']>0
