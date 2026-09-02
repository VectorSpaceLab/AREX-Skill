from buffer_contract import validate_buffers


def test_buffer_contract_rejects_staging_and_accepts_direct_flow():
    buffers = [
        {'name': 'state', 'role': 'state', 'shape': [2, 4], 'producer': 'physics', 'consumer': 'policy', 'direct': True},
        {'name': 'action', 'role': 'action', 'shape': [2, 1], 'producer': 'policy', 'consumer': 'physics', 'direct': True},
        {'name': 'obs', 'role': 'observation', 'shape': [2, 4], 'producer': 'physics', 'consumer': 'policy', 'direct': True},
        {'name': 'reward', 'role': 'reward', 'shape': [2], 'producer': 'task', 'consumer': 'learner', 'direct': True},
        {'name': 'reset', 'role': 'reset', 'shape': [2], 'producer': 'task', 'consumer': 'physics', 'direct': True},
    ]
    assert validate_buffers(buffers, 2)['ok']
    buffers[0]['direct'] = False
    assert not validate_buffers(buffers, 2)['ok']
