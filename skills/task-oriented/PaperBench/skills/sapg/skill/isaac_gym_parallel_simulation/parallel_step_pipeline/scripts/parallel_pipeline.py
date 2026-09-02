def run_parallel_rollout(layout, steps, policy_gain=0.1, reset_threshold=2.5):
    positions = layout['states']['position']
    velocities = layout['states']['velocity']
    rewards = [0.0 for _ in positions]
    resets = 0
    op_count = 0
    for _ in range(steps):
        actions = [-policy_gain * pos for pos in positions]
        op_count += len(actions)
        for i, action in enumerate(actions):
            velocities[i] = 0.9 * velocities[i] + action
            positions[i] = positions[i] + velocities[i]
            rewards[i] += 1.0 / (1.0 + abs(positions[i]))
            op_count += 4
            if abs(positions[i]) > reset_threshold:
                positions[i] = 0.0
                velocities[i] = 0.0
                resets += 1
    return {'positions': list(positions), 'velocities': list(velocities), 'reward_sum': sum(rewards), 'reset_count': resets, 'op_count': op_count}


def sequential_reference(initial_positions, initial_velocities, steps, policy_gain=0.1, reset_threshold=2.5):
    outputs = []
    for pos, vel in zip(initial_positions, initial_velocities):
        layout = {'states': {'position': [pos], 'velocity': [vel]}}
        outputs.append(run_parallel_rollout(layout, steps, policy_gain, reset_threshold))
    return {'positions': [o['positions'][0] for o in outputs], 'velocities': [o['velocities'][0] for o in outputs], 'reward_sum': sum(o['reward_sum'] for o in outputs), 'reset_count': sum(o['reset_count'] for o in outputs), 'op_count': sum(o['op_count'] for o in outputs)}
