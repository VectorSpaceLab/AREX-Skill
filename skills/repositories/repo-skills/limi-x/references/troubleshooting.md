# LimiX cross-cutting troubleshooting

## Import failures

### Symptom

`ModuleNotFoundError: No module named 'inference'`, `model`, `utils`, or `retrieval_extension`.

### Likely cause

The inspected LimiX snapshot is not packaged as an installable distribution. Python must see the active LimiX checkout root.

### Recovery

- Run from the active LimiX checkout root; or
- add the checkout root to `PYTHONPATH`; or
- wrap scripts so they insert the checkout root into `sys.path` before importing LimiX modules.

Use [installation.md](installation.md) and [scripts/check_limix_environment.py](../scripts/check_limix_environment.py) before debugging deeper model issues.

## Checkpoint failures

### Symptom

`FileNotFoundError`, `torch.load` errors, missing `config`/`state_dict` keys, or a task asks for prediction but no `.ckpt` is available.

### Likely cause

`LimiXPredictor` loads the checkpoint in its constructor. Config and data checks can pass even when the checkpoint is absent.

### Recovery

- Ask for or download a local LimiX checkpoint only if network/model-license constraints allow it.
- Match 16M/2M checkpoint family to the selected retrieval config when possible.
- Do not claim inference was verified until the local checkpoint loads and a bounded prediction call completes.

## CUDA and retrieval failures

### Symptom

`ValueError: Retrieval is not supported for CPU inference`, `GPU device not found`, NCCL/DDP initialization errors, CUDA out-of-memory, or unexpectedly slow inference.

### Likely cause

Retrieval configs are GPU-oriented, benchmark entry points guard on CUDA, and full checkpoint inference may need GPU memory even when non-retrieval configs parse on CPU.

### Recovery

- On CPU, switch to a no-retrieval config before constructing `LimiXPredictor`.
- On GPU, run a torch CUDA smoke check first:
  ```bash
  python scripts/check_limix_environment.py --config path/to/config.json --expect-cuda
  ```
- For retrieval OOM, route to [sub-skills/retrieval-optimization/SKILL.md](../sub-skills/retrieval-optimization/SKILL.md) and reduce retrieval length, disable clustering/thresholding, use the 2M family, or switch to non-retrieval.
- For DDP, verify a single-process run before `torchrun`; ensure one process per visible GPU and use the caller's cluster rendezvous policy.

## Flash-attn failures

### Symptom

`Flash attention is not supported. Please install/reinstall flash attention.` or import/build failures around `flash_attn`.

### Likely cause

The source imports without flash-attn and sets `HAVE_FLASH_ATTN=False`; flash-attn kernels are only used when available and on CUDA paths. The wheel must match Python, PyTorch, CUDA, platform, and ABI.

### Recovery

- If the task does not require flash-attn acceleration, use the PyTorch fallback paths and document that acceleration is unavailable.
- If the task requires flash-attn, rebuild the environment with the repo-documented compatible wheel or a source build matched to the installed torch/CUDA stack.
- Do not treat a CPU import as proof that flash-attn acceleration works.

## Data and config failures

### Symptom

Malformed JSON, missing `retrieval_config`, empty pipeline list, all features dropped, all-constant columns, all-NaN feature columns, invalid classification class count, or benchmark datasets silently skipped.

### Recovery

- Use [sub-skills/configuration-preprocessing/scripts/inspect_config.py](../sub-skills/configuration-preprocessing/scripts/inspect_config.py) for JSON config validation.
- Use [sub-skills/benchmark-cli/scripts/validate_dataset_layout.py](../sub-skills/benchmark-cli/scripts/validate_dataset_layout.py) before benchmark-style dataset loops.
- Use [sub-skills/predictor-inference/references/data-formats.md](../sub-skills/predictor-inference/references/data-formats.md) for direct API arrays/dataframes.

## Network/download surprises

### Symptom

A command contacts Hugging Face/ModelScope, creates local cache directories, stalls on downloads, or fails offline.

### Likely cause

The benchmark scripts and examples can auto-download default datasets or checkpoints when paths are omitted.

### Recovery

- Prefer explicit local `--data_dir`, `--model_path`, and `--inference_config_path` values.
- Ask before enabling network downloads or benchmark-scale runs.
- Keep model-license and data-use constraints explicit in final reports.
