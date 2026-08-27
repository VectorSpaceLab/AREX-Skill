# Plotting Training Curves

The repository's `More/plot.py` script reads `.npy` files, turns them into a single dataframe, and draws a seaborn line plot with a confidence interval.

## File naming convention

The original helper expects file names that can be split into:

- algorithm name
- environment name
- seed

A safe convention is:

- `algo_env_seed.npy`

Examples:

- `dqn_CartPole-v0_1.npy`
- `ppo_Pendulum-v1_3.npy`
- `sac_BipedalWalker-v3_7.npy`

## Data layout

The source helper treats each file as a one-dimensional array of average returns.

- column 1: average return
- x-axis: time steps, usually normalized to 0..1 or a similar shared grid
- grouping: algorithm name
- extra labels: environment name and seed

## Bundled helper behavior

Use `scripts/plot_training_curves.py` rather than the source plotting file when you want a safe runtime helper. The bundled script should:

- search a directory tree for `.npy` files
- parse the naming convention
- build a dataframe with algorithm / env / seed columns
- save the plot to a file by default
- avoid opening an interactive window unless explicitly requested

## When to use this helper

- Compare multiple algorithm runs after a training job.
- Sanity-check that saved reward curves were written under the expected naming convention.
- Create a plot without reopening the original repository or running the source `More/plot.py` file directly.
