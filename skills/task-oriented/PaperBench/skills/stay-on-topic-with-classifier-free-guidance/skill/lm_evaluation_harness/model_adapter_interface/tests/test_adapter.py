from adapter import DeterministicLM, dispatch

def test_loglikelihood_order_and_greedy():
    lm=DeterministicLM(scores={'A':1.0,'B':0.0})
    assert dispatch(lm,'loglikelihood',[('q','A'),('q','B')]) == [(1.0, True),(0.0, False)]

def test_generate_until_stop():
    lm=DeterministicLM(generations={'p':'answer\nextra'})
    assert lm.generate_until([('p', {'until':['\n']})]) == ['answer']

def test_unsupported_request_type_rejected():
    lm=DeterministicLM()
    try:
        dispatch(lm, 'embedding', [])
        assert False
    except ValueError as e:
        assert 'unsupported' in str(e)
