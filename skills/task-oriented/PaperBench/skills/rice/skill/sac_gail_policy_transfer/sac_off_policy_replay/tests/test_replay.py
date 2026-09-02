from replay_protocol import build_replay_batch

def test_replay_validation_and_sampling_are_deterministic():
    transitions=[{'state':0,'action':1,'reward':1,'next_state':1,'done':False,'log_prob':-0.5},{'state':1,'action':0,'reward':0,'next_state':2,'done':True,'log_prob':-0.2}]
    result=build_replay_batch(transitions, [1, 0, 3])
    assert result['size'] == 2
    assert [t['state'] for t in result['transitions']] == [1.0, 0.0, 1.0]
    assert transitions[0]['state'] == 0
