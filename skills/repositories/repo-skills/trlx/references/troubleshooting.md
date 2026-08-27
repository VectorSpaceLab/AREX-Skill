# Root troubleshooting for trlX

Use this reference for package-level install/import/backend problems before choosing a workflow sub-skill. For training data/config errors, continue to `sub-skills/training/references/troubleshooting.md`. For NeMo/Megatron/Apex-specific problems, continue to `sub-skills/nemo/references/troubleshooting.md`.

## Install and import

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: trlx` | The active Python is not the environment where trlX was installed. | Run `python -m pip show trlx` with the same Python used by the launcher. Reinstall with `python -m pip install -e .` in a current checkout or install from the public Git URL. |
| `import trlx` fails inside `accelerate launch` but not in an interactive shell | Worker processes use a different environment. | Check `which python`, `python -m pip show trlx`, and `accelerate env` before launching. Activate the intended environment for all ranks. |
| Modern Python fails with old compiled dependencies | trlX 0.7.0-era dependencies target Python 3.9-3.11. | Use a Python 3.9-3.11 environment; avoid Python 3.12/3.13 for this package unless refreshing dependencies intentionally. |
| `pip check` reports packaging/wheel conflicts around `packaging==23.1` | Repository requirements pin older packaging while a new wheel package may require `packaging>=24`. | Prefer a fresh environment. If needed, install a compatible wheel release such as `wheel<0.42`, then rerun `python -m pip check`. |
| `ModuleNotFoundError: pkg_resources` from Ray | Ray 2.x expects `pkg_resources`, which may be absent with newer setuptools. | Install a setuptools release that still provides it, for example `python -m pip install 'setuptools<70'`, then rerun `python -m pip check`. |

## CUDA and PyTorch

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | CPU-only torch wheel, hidden GPUs, or incompatible driver/runtime. | Install a CUDA-capable torch wheel matching the driver and set `CUDA_VISIBLE_DEVICES` deliberately. Run `python scripts/check_trlx_install.py --cuda`. |
| CUDA import works but training OOMs | Model, context, generation, or rollout batch is too large. | Lower `train.batch_size`, set `train.minibatch_size`, lower `method.chunk_size`, lower `seq_length`/`max_new_tokens`, freeze layers, use PEFT, or choose a distributed backend. |
| DeepSpeed launch/config errors | Accelerate YAML and installed deepspeed/torch versions are mismatched. | Start with a small single-process smoke, then a reviewed Accelerate YAML. A100-class GPUs often work better with bf16 than fp16. |
| A source example starts large downloads | Public examples commonly load Hugging Face datasets, model checkpoints, W&B, or reward models. | Convert the example pattern to a small local fixture before full execution; do not run dataset/model downloads unless the user approved network and runtime. |

## W&B, Ray, and sweeps

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Training asks for W&B login or hangs on tracking | `config.train.tracker` defaults to `"wandb"` in many configs. | Set `config.train.tracker = None` for smoke tests or configure W&B credentials/offline mode. |
| `python -m trlx.sweep --help` prints W&B informational banners | The sweep module imports W&B report APIs at module import time. | Treat the banner as normal. For real sweeps, ensure W&B/Ray behavior is acceptable before running. |
| Sweep imports the training script and triggers downloads | The sweep module imports the script module before launching Ray trials. | Put downloads, model loading, and `trlx.train` inside `main(hparams={})`; keep top-level code cheap. |
| Sweep blocks on confirmation | CLI safety prompt. | Pass `-y` / `--assume_yes` only after checking the training script has no unsafe top-level effects. |

## Optional NeMo backend

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ImportError: NeMo is not installed. Please install nemo_toolkit to use NeMo-based trainers.` | trlX registers dummy NeMo trainer entries when the optional NeMo/Apex stack is absent. | Use the training sub-skill if NeMo is not required. If NeMo is required, prepare a separate NeMo/Apex/CUDA environment and use the NeMo sub-skill. |
| Source docs disagree on NeMo branch/version | Historical docs mention different NeMo pins. | Treat the exact NeMo/Apex version as an environment decision. Verify against the chosen torch/CUDA stack before claiming compatibility. |
| `.nemo` or rank-sharded checkpoint cannot load | The checkpoint root, tensor-parallel degree, or rank directory layout is mismatched. | Use `sub-skills/nemo/references/configuration.md` and `sub-skills/nemo/references/troubleshooting.md`. |

## Safe first-response sequence

1. Run `python scripts/check_trlx_install.py` from the skill tree in the target environment.
2. If training configs are involved, run `python sub-skills/training/scripts/inspect_training_config.py --default ppo` or `--yaml <config>`.
3. Set `tracker=None`, choose a small cached/local model, and validate callback/data shapes before distributed launch.
4. Add CUDA/DeepSpeed/Accelerate, then PEFT, then sweeps, only after the single-process path is stable.
5. Route to the NeMo sub-skill only for explicitly NeMo/Megatron tasks.
