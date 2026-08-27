# Troubleshooting

Use this reference when a MimicKit runner command, preset, or backend check fails.

## 1. Import and installation problems

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError` for `mimickit`, `envs`, `learning`, or `engines` | The checkout is not on `PYTHONPATH`, and this repo has no package metadata to install itself as a distribution. | Are you running from a MimicKit checkout? Did you set a repo-style `PYTHONPATH`? | Run from the checkout root or add the checkout root and `mimickit/` directory to `PYTHONPATH`. |
| Source imports work in one shell but not another | The shell environment changed, or the path override was not exported. | Compare the active environment and `PYTHONPATH`. | Reapply the same repo-style path setup in the new shell. |
| `pip install -r requirements.txt` succeeds but imports still fail | Python can see the dependencies but not the source tree. | Confirm the repo root is on the import path. | Use a repo-style `PYTHONPATH`; do not expect package metadata to exist. |

## 2. Optional backend problems

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError: isaacgym` | Isaac Gym is not installed. | Is the selected engine config the Isaac Gym YAML? | Install Isaac Gym or switch to an environment / backend that is actually present. |
| `ModuleNotFoundError: isaaclab` or `isaacsim` | Isaac Lab / Isaac Sim is not installed. | Is the selected engine config the Isaac Lab YAML? | Install Isaac Lab / Isaac Sim or switch to another backend. |
| `ModuleNotFoundError: newton` or `warp` | Newton / Warp is not installed. | Is the selected engine config the Newton YAML? | Install Newton + Warp or switch to a different backend. |
| Backend import succeeds but the runner still fails early | The engine import order or asset prerequisites are wrong. | Is the runner being wrapped in a way that changes import order? | Keep the bundled runner flow and verify the backend / asset combo. |

## 3. Config and preset mismatches

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| `Unsupported engine` | `engine_name` in the engine YAML does not match the builder branch. | Does the YAML contain `isaac_gym`, `isaac_lab`, or `newton`? | Pick one of the bundled engine YAMLs or fix the config name. |
| `Unsupported env` | `env_name` in the environment YAML does not match a builder branch. | Does the env YAML point to a known environment family? | Use a valid env config from the checkout. |
| `Unsupported agent` | `agent_name` in the agent YAML does not match a builder branch. | Is the YAML one of the supported agent families? | Switch to a valid agent config. |
| `Unsupported mode` | `--mode` is not `train` or `test`. | Did the command use some other value? | Use `train` or `test` only. |
| `Failed to load args from: ...` | The `--arg_file` path is wrong or the preset file is malformed. | Does the file exist? Are comments on their own lines? | Fix the path, then simplify the preset so each line is just flags and values. |
| An override does not take effect | The same key was already loaded earlier, and first-write wins. | Is the CLI override spelled exactly the same as the preset key? | Put the override on the CLI, and avoid duplicate keys in the preset. |

## 4. Asset / data problems

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| `Unsupported asset format` | The chosen engine does not support the asset file extension. | Does the asset extension match the backend? | Use `.xml` for Isaac Gym / Newton, `.usd` for Isaac Lab, or `.urdf` for Newton. |
| Env build fails because a motion file is missing | The environment YAML points at an external motion clip or dataset that is not present. | Does the referenced motion asset exist under the expected data tree? | Download the missing motion data or change the config to a present file. |
| A checkpoint path is missing in test mode | `--model_file` was not supplied or the file is absent. | Does the checkpoint exist? | Pass the correct checkpoint path before running `--mode test`. |
| A vault / task config references a missing object file | The checkout only contains a partial asset set. | Is the required object asset one of the known missing external files? | Obtain the missing asset or use a different config. |

## 5. Device and distributed failures

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| Distributed init hangs | Two jobs are fighting for the same port, or the device list is inconsistent. | Is `--master_port` unique? Are all workers using the same device family? | Set a fixed free port and keep the device list consistent. |
| `nccl` / `gloo` init errors | The chosen backend does not match the device type or the platform. | Are you using `cpu` vs `cuda:{i}` correctly? | Use `cpu` for gloo or `cuda:{i}` for NCCL; on Windows, CUDA may fall back to gloo. |
| CUDA training starts but the command is slow or memory-heavy | `--num_envs` is too large for the selected backend or task. | Is the backend parallel-friendly? | Reduce `--num_envs` or switch to a backend / preset that supports the larger batch. |

## 6. Logging and video failures

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| No viewer appears | `--visualize false` was used or the backend is running headless. | Did you intentionally disable visualization? | Turn `--visualize true` back on only if the backend supports interactive rendering. |
| Video is not recorded | The engine disables recording when visualization is enabled. | Are `--visualize true` and `--video true` both set? | Use headless mode for recording: `--visualize false --video true`. |
| TensorBoard shows no files | The logger was not set to `tb`, or the output directory was not used consistently. | Is `--logger tb` selected? | Use the TensorBoard logger and point TensorBoard at the training output directory. |
| W&B run does not appear | W&B is not logged in, or the environment cannot reach W&B. | Is the `wandb` package installed and authorized? | Use `--logger wandb` only when online logging is available. |

## 7. Safe layout-check failures

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| The safe checker reports a missing core file | The checkout layout is incomplete or the wrong repo root was passed. | Did you point the checker at the real MimicKit checkout root? | Re-run the checker with the correct repo root. |
| The safe checker reports a missing config referenced by a preset | A repo preset points at a config that was renamed or deleted. | Is the referenced YAML still present? | Restore the config or update the preset. |
| The safe checker warns about missing external data | The repo intentionally does not ship all motion / model / object assets. | Are the missing files under `data/motions/`, `data/models/`, `data/logs/`, or external object assets? | Treat the warning as a data-preparation task, not as a parser bug. |

## 8. Fast diagnosis order

When a runner command fails, check in this order:

1. Is the repo import path set correctly?
2. Is the selected backend installed?
3. Does the YAML triad match the backend and task?
4. Does the preset reference only files that exist in this checkout?
5. Are `--visualize`, `--video`, `--devices`, and `--master_port` consistent with the runtime plan?

That order catches most MimicKit runner problems before you chase simulator-specific details.
