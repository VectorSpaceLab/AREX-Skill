# Optimization workflows

## Offline trajopt

Resolve robot/task YAMLs through the solver config factory, build a trajectory
optimizer, set a start state and pose/c-space goal, and solve with a small seed
count. Validate the returned trajectory at its interpolated controller rate,
not only at optimizer knots. Use the solver's dt constraints for timing.

## Receding-horizon MPC

Initialize current state and goal, call warm-start solve each cycle, consume
only the next validated action, then update current state from measured robot
state. If a solve fails, use the solver's safe-deceleration trajectory and do
not command an arbitrary stale action. Reset the seed/shape when the number of
environments changes.

## Custom optimization

Implement or reuse the Rollout protocol when a custom differentiable objective
is needed. Keep action shape `(batch, horizon, action_dim)`, expose bounds/dt,
return metrics, and separate optimization costs from convergence diagnostics.
Start from a Rosenbrock-like tiny objective before composing robot collision.
