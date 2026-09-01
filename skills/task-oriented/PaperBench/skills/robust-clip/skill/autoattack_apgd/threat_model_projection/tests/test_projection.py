from projection import project

def test_linf_projection_and_box():
    adv, info = project([0.5,0.1],[1.2,-0.5], norm='Linf', eps=0.2)
    assert adv == [0.7, 0.0]
    assert max(info['norms']) <= 0.2

def test_l2_projection_scales():
    adv, info = project([0.0,0.0],[3.0,4.0], norm='L2', eps=1.0, upper=10.0)
    assert abs(info['norms'][0]-1.0) < 1e-9
    assert abs(adv[0]-0.6) < 1e-9 and abs(adv[1]-0.8) < 1e-9
