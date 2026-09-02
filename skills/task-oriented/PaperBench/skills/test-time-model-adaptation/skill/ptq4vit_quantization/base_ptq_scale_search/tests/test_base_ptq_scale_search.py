from calibrate import search_scale

def test_search_selects_candidate():
    r=search_scale([0.0,0.49,1.01],[0.1,0.25,0.5],bits=4)
    assert r['scale'] in [0.25,0.5]
    assert len(r['trace'])==3
