def refine(initial_state, condition, scale_factor, weight, steps=4):
    target_prior = float(condition) * float(scale_factor)
    state = float(initial_state)
    trajectory = []
    for step in range(int(steps)):
        correction = float(weight) * (state - float(condition)) / (step + 1.0)
        state = 0.65 * state + 0.35 * target_prior - 0.1 * correction
        trajectory.append({'step': step + 1, 'state': state, 'target_prior': target_prior, 'correction': correction})
    return {'trajectory': trajectory, 'final': state}
