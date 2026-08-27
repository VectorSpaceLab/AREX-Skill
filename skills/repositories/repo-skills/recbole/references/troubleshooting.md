# RecBole Cross-Cutting Troubleshooting

Use this root reference when the failure is not clearly owned by one sub-skill.
Then route to the nearest detailed troubleshooting reference.

## Import and dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'recbole'` | RecBole is not installed in the active Python environment. | Install `recbole` or install the local package for development, then run `python scripts/check_recbole_env.py`. |
| `ModuleNotFoundError` for `torch` | PyTorch is missing or installed in a different environment. | Install a CPU or CUDA PyTorch build compatible with the environment and requested backend. Do not claim GPU readiness from a CPU-only torch build. |
| Importing `recbole.quick_start` fails in Ray with `pkg_resources` missing | Older Ray versions import `pkg_resources`; very new setuptools may remove it. | Install a setuptools version that still exposes `pkg_resources`, or upgrade Ray only after checking RecBole compatibility. |
| Ray fails with `numpy` attributes such as `np.bool8` | Ray version is incompatible with NumPy 2.x. | Use a NumPy 1.x version compatible with the Ray version, or upgrade Ray only with a full compatibility check. |
| `ModuleNotFoundError: hyperopt` during tuning | Hyperopt optional tuning dependency is missing. | Install Hyperopt or use non-HyperTuning workflows. |
| `ModuleNotFoundError: xgboost` or `lightgbm` | External-library model dependency is missing. | Install the matching package or choose a built-in neural/tree-free model. Route model choice to `models-and-customization`. |

## Backend and hardware failures

- CPU is valid for most configuration, data, model-resolution, and bounded
  training/evaluation smoke checks.
- CUDA is optional acceleration unless the user explicitly asks to verify GPU,
  multi-GPU, Ray GPU, or a model path with no CPU substitute.
- `use_gpu: true` is not proof of CUDA use. Inspect the resolved
  `config["device"]` and verify `torch.cuda.is_available()`.
- If a run OOMs on GPU, reduce `train_batch_size`, `eval_batch_size`,
  embedding/hidden sizes, sequence length, or switch evaluation mode before
  blaming the model registry.
- Ray GPU trials require compatible CUDA-enabled torch and enough free devices;
  `resources_per_trial={"gpu": 1}` is a scheduling request, not a dependency
  installer.

## Route-choice failures

| User task shape | Correct route |
| --- | --- |
| Atomic file headers, missing dataset files, `load_col`, config override priority, data caching | `sub-skills/configuration-and-data/` |
| Running `run_recbole`, no-checkpoint CPU smoke, metrics, checkpoints, save/load, case study, HPO, Ray, significance testing | `sub-skills/training-evaluation-and-tuning/` |
| Choosing `BPR` vs `SASRec` vs `DeepFM` vs `KGAT`, model registry, custom recommender/trainer/dataloader/sampler/metric | `sub-skills/models-and-customization/` |

When a task spans all three, solve it in this order:

1. Validate data/config.
2. Select or customize the model.
3. Run/evaluate/tune.

## Safe diagnostic sequence

```bash
python scripts/check_recbole_env.py --models BPR --check-optional
python sub-skills/configuration-and-data/scripts/validate_atomic_dataset.py \
  /path/to/dataset-root/my_dataset --dataset my_dataset --task-family general
python sub-skills/training-evaluation-and-tuning/scripts/recbole_train_eval_smoke.py \
  --model BPR --dataset my_dataset --data-path /path/to/dataset-root --dry-run-config
```

Only pass `--run` to training/tuning helpers after the user accepts the runtime,
write locations, and compute budget.
