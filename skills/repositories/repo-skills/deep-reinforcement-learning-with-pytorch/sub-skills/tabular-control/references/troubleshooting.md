# Tabular Control Troubleshooting

## pandas import fails

The original 1D chain scripts build their Q-table with `pandas.DataFrame`. The bundled demo does not require pandas and uses a plain NumPy array instead.

If you intentionally run the historical source files unchanged, install pandas in the inspection environment or switch to the bundled demo.

## matplotlib or headless display problems

The source scripts call `plt.show()` after training. In a headless shell or CI session this can hang or fail because there is no interactive display backend.

For this sub-skill, the safe path is to keep plotting out of the default run. If you are reproducing the original script anyway, prefer a non-interactive backend such as `Agg` and save the figure instead of showing it.

## Animation is too slow

The historical `update_env` helper sleeps on every step. That is useful for a classroom animation, but it makes tiny experiments feel sluggish.

Use the bundled demo with rendering disabled by default. If you enable rendering, keep the delay at `0` unless you really want animation.

## Terminal-state counting looks off

Watch for off-by-one mistakes when the agent moves from the penultimate state into the terminal state.

Rules to keep straight:
- count one transition per environment step
- do not update the terminal row as if it were a normal state
- the terminal transition should be handled once, then the episode should stop

If the episode length keeps increasing unexpectedly, inspect the terminal branch before the Q-update.

## Epsilon-greedy choice or action naming looks wrong

The source uses `left` and `right` as the only actions in the 1D chain, and `up`, `right`, `down`, `left` in GridWorld.

Common mistakes:
- mixing string labels with numeric indices without a conversion layer
- treating the `EPSILION` typo as a different concept from the exploration rate
- choosing the greedy action from an empty or all-zero row without a tie-break rule

The bundled helpers normalize the action handling and break ties among equal Q-values randomly.

## GridWorld shape or scalar-action errors

If `GridWorld` raises a shape error, check the matrix dimensions first:
- transition matrix: `4 x 4`
- reward matrix: same shape as the world
- state matrix: same shape as the world

If a step call fails because the action looks like a one-element array, coerce it to a scalar before indexing the transition rules. The bundled helper already does this.
