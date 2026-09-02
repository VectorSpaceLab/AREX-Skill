from guided_score import guided_score, guidance_audit

def test_w_zero_identity_and_vector():
    assert guided_score([1,2],[10,20],0)==[1,2]
    assert guided_score(2.0, 1.0, 3.0)==5.0

def test_shape_validation_and_audit():
    try:
        guided_score([1],[1,2],1)
        assert False
    except ValueError:
        pass
    a=guidance_audit(2,1,0.5)
    assert a['guided']==2.5 and 'conditional' in a['formula']
