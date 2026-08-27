# Troubleshooting

## Gym and optional extras

### A tutorial imports Gym or TensorFlow Probability that is not installed

That is expected in the minimum CPU-only scope. Keep the bundled smoke on `tensorlayer.rein` helpers and treat the long tutorials as reference-only unless the user wants the full RL stack.

### The environment version differs from the tutorial

RL tutorials often target older Gym APIs. Prefer the bundled smoke helpers and update the tutorial only when you explicitly need the full example.

## Stochastic output issues

### Action sampling returns different values each run

Use a probability vector with a deterministic 1.0 entry when you need a stable smoke. Otherwise the helper is stochastic by design.

### Reward-discount checks do not match your mental model

Confirm the `mode` argument and whether the reward vector contains reset points. The helper has a resetting mode and a no-reset mode.

## Long-running example issues

### Training appears to hang

Many RL tutorials are long-running and may block on environment setup or episode loops. Keep the smoke helper small and synthetic before you investigate the full tutorial.
