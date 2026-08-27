# Setup and Cross-cutting Troubleshooting

This reference covers repository-wide setup and failure modes shared by the GridWorld, CartPole, Atari, and hard-exploration Atari workflows.

## Runtime shape

The repo is a collection of standalone scripts. It declares a distribution name and dependency set in project metadata, but the source layout is not a conventional import package. A future agent should not rely on `import reinforcement_learning`; use the workflow guidance and bundled smoke scripts instead.

Recommended public setup pattern:

```bash
# In a normal clone of the repository, when the user wants to run original workflows:
uv sync
uv run python --version        # should be Python 3.11.x

# To run this generated skill's self-contained dependency check:
python scripts/check_reinforcement_learning_environment.py
```

Core dependency families:

- PyTorch/TorchVision for neural policies, value functions, CNNs, RND, and GRU policies.
- Gymnasium plus `ale-py` for CartPole and Atari environments.
- Pygame for GridWorld and CartPole/Atari human rendering event handling.
- NumPy for tabular algorithms, rollouts, buffers, returns, and archive logic.
- OpenCV headless for hard-Atari frame preprocessing/demo support.
- envpool for high-throughput hard-Atari PPO+RND vectorized training.
- W&B only when the user explicitly enables Atari logging.

## Flat script repository warning

If `pip install -e .` fails with a message similar to "Multiple top-level packages discovered in a flat-layout", do not treat that as a broken algorithm implementation. The examples are intended to be run as scripts from their workflow directories. Use `uv sync` to install dependencies, or install the dependency set in an isolated environment, then run the relevant workflow entrypoint.

For generated skill verification, prefer the bundled smoke helpers because they reimplement tiny invariants without depending on source file imports.

## Python version

The metadata pins Python 3.11. If dependency resolution tries Python 3.13 or another version, expect compiled wheel failures around PyTorch, Gymnasium/Atari, envpool, or OpenCV. Recreate the environment with Python 3.11 before debugging deeper algorithm issues.

## Rendering and display

Symptoms:

- Pygame reports missing video device or cannot open a display.
- A window close button does not terminate immediately.
- `--render` or `--test` is much slower than training.

Recovery:

- Avoid `--render` on headless servers; use non-render training or bundled smoke scripts.
- The CartPole/Atari helpers pump Pygame QUIT events when a display is initialized, but this only matters for human render/test loops.
- GridWorld DP examples are GUI-button driven; use the GridWorld smoke helper when you only need to validate formulas or update steps.

## Atari ROMs and ALE

Importing `ale_py` is not the same as having usable Atari ROM assets. If actual Atari env creation/reset fails:

1. Confirm the requested environment key is valid for the workflow: standard Atari uses `breakout` or `pong`; hard Atari uses `montezuma`, `pitfall`, `private_eye`, or the Go-Explore-specific `montezuma_goexplore`.
2. Confirm Gymnasium/ALE ROM installation/licensing is satisfied in the user's environment.
3. Separate dependency import checks from emulator execution. The bundled smoke scripts deliberately validate model and data invariants without starting ALE.

## Device/backend selection

Standard and hard Atari helpers choose `cuda` when available, then `mps`, then `cpu`, unless a device override is supplied. Treat CUDA/MPS as acceleration, not as proof that training will reach benchmark scores. CPU can validate model shapes and most algorithm invariants; full Atari throughput and benchmark reproduction are hardware- and runtime-sensitive.

Common device fixes:

- Force CPU for debugging with the workflow's `--device cpu` option when available.
- If CUDA is visible but tensor allocation fails, check driver/runtime compatibility and PyTorch wheel tags.
- MPS benchmark notes in the README describe Apple hardware and do not transfer directly to Linux CUDA hosts.

## W&B logging

Atari workflows only contact W&B when the user passes the logging flag. If W&B errors appear:

- Omit the flag for offline/local runs.
- Run W&B login only when the user explicitly wants network logging and has credentials.
- Do not copy API keys or login state into scripts, configs, or generated skill files.

## Checkpoint and artifact locations

Most simple scripts save checkpoint files near the workflow being executed. Hard-Atari run-managed workflows can write:

- `metrics.jsonl` for streamed scalar rows.
- `ckpt/latest.pt` and optional milestone/best checkpoints.
- `final.json` with `frames_total`, `frames_unit`, `gate_metric`, `K`, `value_mean`, `value_std`, and `episodes_counted`.

Do not reuse a checkpoint across algorithms unless the sub-skill documents the exact loader shape. For example, CartPole A2C stores actor and critic state dictionaries together, while DQN/PPO checkpoints are single model state dictionaries.

## Benchmark expectations

The repo includes benchmark notes, but this skill's verification only checks operating invariants. Full runs can take hours, require emulator assets, create large buffers/checkpoints, use GPU/MPS/CPU resources differently, and be sensitive to seeds and protocol choices. Report smoke success as "interface/invariant passed," not as convergence or benchmark reproduction.
