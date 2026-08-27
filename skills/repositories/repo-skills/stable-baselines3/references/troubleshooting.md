# Cross-Cutting Troubleshooting

Read this for install/import and runtime issues that affect several SB3 workflows. For workflow-specific failures, use the nearest sub-skill troubleshooting reference.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | PyTorch is not installed or the wrong Python is active | Install SB3 in the target environment with `pip install stable-baselines3`, then run `python -m pip check`. |
| `ModuleNotFoundError` for `tqdm`, `rich`, `tensorboard`, `cv2`, `pygame`, `ale_py`, `pandas`, or `matplotlib` | Optional feature requires the `extra` extra | Install `pip install 'stable-baselines3[extra]'` only when those features are needed. |
| Training unexpectedly uses CPU or warns about GPU for PPO/A2C | SB3 auto-selects device; on-policy algorithms are often faster on CPU | Pass `device='cpu'` for small MLP PPO/A2C jobs unless a measured GPU workload justifies CUDA. |
| Rendering fails or opens no window | Environment lacks compatible `render_mode` or optional render dependencies | Create Gymnasium envs with an explicit render mode and install needed extras; do not render in smoke tests. |

## Gymnasium and SB3 API Differences

SB3 wraps non-vectorized envs into `VecEnv` internally. `VecEnv.reset()` returns only observations, while Gymnasium `Env.reset()` returns `(obs, info)`. `VecEnv.step()` returns `(obs, rewards, dones, infos)` and automatically resets completed environments; terminal observations are stored in `infos[i]['terminal_observation']`.

## Choosing the Right Next Reference

- Algorithm/action-space or short training errors: `sub-skills/training-and-algorithms/references/troubleshooting.md`.
- Custom env, `check_env`, image, Dict, NaN, or vectorization errors: `sub-skills/environments-and-vectorization/references/troubleshooting.md`.
- Evaluation, callbacks, logger, save/load, or portability errors: `sub-skills/evaluation-and-persistence/references/troubleshooting.md`.
- `policy_kwargs`, feature extractor, action noise, gSDE, or HER errors: `sub-skills/policies-and-customization/references/troubleshooting.md`.

## Minimal Diagnostic

Run the bundled doctor to verify public imports, optional extras, CUDA visibility, and key signatures:

```bash
python scripts/sb3_doctor.py --check extras --check signatures
```
