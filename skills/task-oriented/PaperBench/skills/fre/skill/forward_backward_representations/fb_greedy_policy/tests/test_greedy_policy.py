from greedy_policy import greedy_policy

def test_greedy_policy_and_ties():
    out = greedy_policy([[1,0],[0,1],[1,1],[1,1]],[0,2],2,2)
    assert out['policy'] == [1,0]
    assert out['ties'][1] == [0,1]
