from group_concepts import group

def test_grouping_purity_and_unknowns():
    out=group([{'token':'Ġcat'},{'token':'dog'},{'token':'x'}], {'animal':['cat','dog']})
    assert out['best_concept']=='animal'
    assert out['purity']==2/3
    assert out['unresolved']==['x']
