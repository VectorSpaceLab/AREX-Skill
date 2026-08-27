# Habitat-Lab Cross-Cutting Troubleshooting

## Import Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'magnum'` | Habitat-Sim is missing or installed for an incompatible Python | Use Python 3.9 and install `habitat-sim withbullet` from the documented conda channels before importing `habitat` |
| `ModuleNotFoundError: No module named 'habitat_sim'` | Core package installed without simulator backend | Install Habitat-Sim; do not debug Habitat-Lab source first |
| `ImportError` from `habitat_baselines` | Baselines extras such as PyTorch or TensorBoard are missing | Install `habitat-baselines` and inspect `baselines-training-and-evaluation` troubleshooting |
| `ImportError` from `habitat_hitl` | HITL dependencies or Habitat-Sim graphics modules are missing | Install `habitat-hitl`, `websockets`, `aiohttp`, and verify Habitat-Sim imports |

## Config And Hydra Failures

- If Hydra reports a missing config, verify whether the config belongs to core Habitat or Habitat-Baselines and use the correct loader.
- If an override fails, compose the config with a bundled probe and inspect the key path before launching simulation or training.
- Legacy Baselines `--exp-config` and `--run-type` commands must be converted to `--config-name` and `habitat_baselines.evaluate=True/False`.

## Simulator, Graphics, And Hardware Failures

- `WindowlessContext: Unable to create windowless context` or EGL device errors usually indicate driver, `libglvnd`, container GPU passthrough, or display configuration issues.
- On Linux, check `nvidia-smi`, EGL/GLVND installation, and whether the runtime can see a GPU.
- For headless or remote HITL use, separate import/config probes from full viewer launch; full viewers need display/window/websocket resources.
- NVIDIA A100 black-square rendering artifacts are documented as a driver/CUDA issue; newer CUDA drivers may be required.

## Data Failures

- Missing scenes and missing task episodes are different. A scene dataset can exist while task episode JSON is absent, and vice versa.
- Use config probes to inspect `data_path`, `scenes_dir`, and simulator scene keys before running Env construction.
- Do not auto-download large datasets or start benchmark scripts without explicit user intent.

## Multiprocessing And Runtime Hangs

- Vectorized environments can hide worker exceptions. Set `HABITAT_ENV_DEBUG=1` to use a slower but more verbose threaded path while debugging.
- For Baselines distributed or DD-PPO runs, verify NCCL/GPU/network prerequisites separately from config composition.

## Gym Warning

The repo uses Gym `0.22.x`, which emits the upstream warning that Gym is unmaintained. Treat the warning as expected for this version unless it is accompanied by an actual failure.
