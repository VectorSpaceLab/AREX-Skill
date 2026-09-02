from fisher_mask_search import search

def test_zero_budget_prunes_all_units():
    got=search([0.2,0.3],[0.4],2,1,0)
    assert got['head_mask'] == [0,0]
    assert got['filter_mask'] == [0]
    assert got['remaining_cost'] == 0
