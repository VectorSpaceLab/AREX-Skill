from parallel_pipeline import run_parallel_rollout, sequential_reference


def test_parallel_matches_sequential_reference():
    layout = {'states': {'position': [0.5, -0.25, 0.75], 'velocity': [0.0, 0.1, -0.1]}}
    initial_p = list(layout['states']['position'])
    initial_v = list(layout['states']['velocity'])
    batched = run_parallel_rollout(layout, 5)
    seq = sequential_reference(initial_p, initial_v, 5)
    assert batched['positions'] == seq['positions']
    assert batched['velocities'] == seq['velocities']
    assert abs(batched['reward_sum'] - seq['reward_sum']) < 1e-12
