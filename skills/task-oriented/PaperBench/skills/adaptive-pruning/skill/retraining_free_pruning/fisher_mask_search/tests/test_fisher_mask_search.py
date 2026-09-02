from fisher_mask_search import search, exhaustive

def test_matches_exhaustive():
    hs=[0.9,0.1,0.4]; fs=[0.2,0.8]
    got=search(hs,fs,2,1,4)
    best=exhaustive(hs,fs,2,1,4)
    assert abs(got['pruned_fisher_loss']-best[0]) < 1e-9
    assert got['remaining_cost'] <= 4

def test_rejects_negative():
    try: search([-1], [1], 1, 1, 1)
    except ValueError: return
    assert False
