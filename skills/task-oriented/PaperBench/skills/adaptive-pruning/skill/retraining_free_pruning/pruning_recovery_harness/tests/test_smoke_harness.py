from smoke_harness import mechanism_pass_rate

def test_pass_rate():
    assert mechanism_pass_rate({'a':True,'b':False}) == 0.5
