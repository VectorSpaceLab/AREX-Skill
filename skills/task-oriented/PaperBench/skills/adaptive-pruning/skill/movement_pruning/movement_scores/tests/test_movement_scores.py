from movement_scores import update_movement_scores

def test_sign_cases():
    r=update_movement_scores([1,1,-1,-1],[0,0,0,0],[-.5,.5,.5,-.5],lr_score=1)
    deltas=[d['score_delta'] for d in r['diagnostics']]
    away=[d['away_from_zero'] for d in r['diagnostics']]
    assert away==[True,False,True,False]
    assert deltas[0]>0 and deltas[2]>0 and deltas[1]<0 and deltas[3]<0
