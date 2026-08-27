# Tabular Control Notes

## Shared toy chain

The 1D chain examples in `Q-learning.py` and `Sarsa.py` use the same basic setup:

- states are numbered `0 .. N-1`
- actions are `left` and `right`
- the agent starts at state `0`
- moving right from the penultimate state enters the terminal state at the last index
- the final transition gives reward `+1`
- all other transitions give reward `-0.5`
- the helper counts environment transitions, not screen renders

The source scripts differ mainly in the update rule and in their default `N_STATE` value.

## Q-learning vs Sarsa

| Algorithm | Update target | Policy meaning |
| --- | --- | --- |
| Q-learning | `r + gamma * max_a' Q(s', a')` | off-policy target; the behavior can explore while the target stays greedy |
| Sarsa | `r + gamma * Q(s', a')` using the next sampled action | on-policy target; the target follows the same epsilon-greedy behavior policy |

When comparing the two, keep the environment, seed, `alpha`, `gamma`, and exploration rate fixed. Only the bootstrapping target should change.

## Update loop

```text
for each episode:
    state = start_state
    action = epsilon_greedy(Q[state])
    while not done:
        next_state, reward, done = transition(state, action)
        if algorithm == q_learning:
            target = reward if done else reward + gamma * max(Q[next_state])
            next_action = epsilon_greedy(Q[next_state]) only for the next loop iteration
        else:
            next_action = epsilon_greedy(Q[next_state]) if not done else None
            target = reward if done else reward + gamma * Q[next_state, next_action]
        Q[state, action] += alpha * (target - Q[state, action])
        state = next_state
        action = next_action when one was sampled
```

The bundled demo uses the standard convention that `epsilon` is the probability of a random exploratory action. The original source names the variable `EPSILION`, which is easy to misread; the helper keeps the naming explicit.

## GridWorld helper

`gridworld.py` is a separate helper for the 2D world class from the source checkout.

- action space size is `4`
- action indices are `0=up`, `1=right`, `2=down`, `3=left`
- `transition_matrix` must be `4 x 4`
- `reward_matrix` must match the world shape
- `state_matrix` must match the world shape
- `state_matrix` uses `0` for walkable cells, `-1` for obstacles, and `+1` for terminal cells
- `reset(exploring_starts=True)` should choose a walkable cell
- `render()` should be safe to call in headless runs and should not require an animation delay

## Source quirks fixed in the bundled helpers

- the demo scripts do not run on import
- sleep or animation delay is opt-in rather than automatic
- action sampling is coerced to a scalar before indexing the GridWorld transition rules
- terminal-state bookkeeping uses an explicit done flag instead of relying on a truthy array
- the original `setPosition` undefined-name bug is corrected in the fixture-friendly helper

## Practical reading order

1. Read this file if you want the update rules and environment semantics.
2. Open `scripts/tabular_control_demo.py` if you want the runnable toy example.
3. Open `scripts/gridworld.py` if you want the 2D helper or a fixture-friendly class to copy.
