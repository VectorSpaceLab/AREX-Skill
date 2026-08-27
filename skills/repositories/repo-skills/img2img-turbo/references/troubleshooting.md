# Troubleshooting

## Purpose

Use this cross-cutting reference for environment, import, CUDA, and source-checkout failures that affect more than one img2img-turbo workflow.

## Common failures and fixes

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError` for `pix2pix_turbo`, `cyclegan_turbo`, `image_prep`, `model`, or `my_utils.*` | The source checkout is not on `PYTHONPATH`. | Add `src/` to `PYTHONPATH` or run the bundled environment checker, which does it automatically. |
| `RuntimeError: operator torchvision::nms does not exist` | Torch / TorchVision wheel mismatch. | Reinstall a matched CUDA-capable `torch` and `torchvision` pair, then re-run the checker. |
| `ImportError: cannot import name 'cached_download'` or `split_torch_state_dict_into_shards` | Hugging Face package versions are out of sync with `diffusers`, `transformers`, or `accelerate`. | Re-pin the Hugging Face stack to a mutually compatible combination and re-run the checker. |
| `ModuleNotFoundError: No module named 'pkg_resources'` while loading `gdown` / `vision_aided_loss` | `setuptools` is too new or otherwise missing the legacy API expected by that dependency chain. | Install a compatible `setuptools` version, then verify imports again. |
| CUDA is unavailable but the workflow tries to run inference or training | The source code is CUDA-oriented and has no verified CPU substitute for actual generation/training. | Use a CUDA-capable environment and re-run the environment checker with `--require-cuda`. |
| `accelerate launch` opens with multi-GPU defaults or reports a port conflict | Persistent Accelerate defaults or a busy main process port. | For training, pass explicit `--num_processes` and `--main_process_port`; for inspection, use direct `python src/... --help` or the bundled checker instead of `accelerate launch --help`. |
| Dataset download helper refuses to run | `--yes` was omitted or the target path would be unsafe to overwrite. | Review the helper with `--help`, then rerun with `--dataset`, `--output-dir`, and `--yes`. |
| A pretrained selector is used with the wrong custom/pretrained flags | Paired and unpaired branches have different selector rules. | Open the relevant sub-skill reference and validate the selector / prompt / direction combination before running the source script. |

## How to recover

1. Run [`scripts/check_environment.py`](../scripts/check_environment.py) with the source-checkout path passed via `--repo-root` and the scope that matches your task.
2. Fix the specific import, version, or CUDA mismatch it reports.
3. Re-run the checker before trying the source scripts again.
4. If the failure is specific to paired inference, unpaired inference, or training data, use the nearest sub-skill troubleshooting page for the workflow-specific recovery steps.

## When to escalate

- If the environment checker fails because CUDA is absent, move to a GPU-capable host or narrow the task to documentation-only planning.
- If a task needs model downloads or full training, ask before performing those network or long-running actions.
- If a failure is only about paired or unpaired command arguments, do not repair the environment first; fix the command and re-run the safe helper.
