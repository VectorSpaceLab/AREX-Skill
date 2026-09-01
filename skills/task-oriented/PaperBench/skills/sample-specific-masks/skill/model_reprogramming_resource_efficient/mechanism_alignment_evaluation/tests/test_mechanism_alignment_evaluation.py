from mechanism_check import alignment_distance, check

def test_mechanism_check():
    tr={'source_unchanged':True,'params_before':{'a':0},'params_after':{'a':1},'loss_before':1,'loss_after':.5,'accuracy_after':.75}
    c=check(tr,.7)
    assert all(c.values())
    assert alignment_distance([[0,0],[2,2]], [[1,1]]) == 0
