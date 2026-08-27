---
name: limi-x
description: "Use LimiX for structured/tabular foundation-model inference,
  configuration, retrieval tuning, and benchmark-style workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LimiX repo skill

Use this skill when a task involves LimiX, LimiXPredictor, LDM structured-data foundation models, tabular classification/regression, missing-value imputation, LimiX inference configs, retrieval-based ensemble inference, or LimiX benchmark-style dataset loops.

LimiX is a source-repo style project rather than a packaged PyPI distribution. Future agents should treat this skill as self-contained operating guidance: read the bundled references/scripts here first, then apply them to the user's active LimiX checkout, local checkpoint, or local tabular data. Do not assume model checkpoints or benchmark datasets have already been downloaded.

## First checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.
2. Read [references/installation.md](references/installation.md) when installing dependencies, checking CUDA/flash-attn, or explaining why source imports fail.
3. Read [references/model-and-config-overview.md](references/model-and-config-overview.md) to choose model family, task, and inference config style.
4. Run [scripts/check_limix_environment.py](scripts/check_limix_environment.py) for a safe import/config/backend diagnostic before full checkpoint inference.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting checkpoint, CUDA, source-layout, download, and data-size failures.

## Route by task

| User intent | Load this sub-skill | Why |
| --- | --- | --- |
| Direct Python API prediction with `LimiXPredictor`, including classification, regression, or MVI | [sub-skills/predictor-inference/SKILL.md](sub-skills/predictor-inference/SKILL.md) | Owns constructor/predict signatures, local checkpoint/config recipes, return shapes, and MVI helpers. |
| Validate or run benchmark-style dataset-folder workflows | [sub-skills/benchmark-cli/SKILL.md](sub-skills/benchmark-cli/SKILL.md) | Owns dataset-root layout, classification/regression CLI flags, output CSVs, metric interpretation, and safe layout validation. |
| Tune retrieval-based ensemble inference or preview search-space parameters | [sub-skills/retrieval-optimization/SKILL.md](sub-skills/retrieval-optimization/SKILL.md) | Owns retrieval config keys, attention/retrieval classes, Optuna search flow, and memory/OOM guidance. |
| Choose, inspect, generate, or debug inference config JSON and preprocessing transforms | [sub-skills/configuration-preprocessing/SKILL.md](sub-skills/configuration-preprocessing/SKILL.md) | Owns config catalog, config schema, preprocessing classes, CPU-safety checks, and config validator/generator scripts. |

## Minimal setup shape

A practical LimiX session usually needs:

- a LimiX source checkout or equivalent import path exposing `inference`, `model`, `utils`, and `retrieval_extension` modules;
- Python 3.12-era dependencies from the project's environment/Docker guidance, especially PyTorch, scikit-learn, NumPy, pandas, SciPy, einops, tqdm, huggingface-hub, kditransform, hyperopt, and optional Optuna;
- a local LimiX checkpoint (`LimiX-16M.ckpt` or `LimiX-2M.ckpt`) when running predictions;
- a config JSON list compatible with the task and device;
- CUDA/GPU for retrieval configs, DDP, flash-attn acceleration, and practical full checkpoint inference; CPU is only appropriate for non-retrieval setup/config checks and limited non-retrieval experimentation.

Safe diagnostic:

```bash
python scripts/check_limix_environment.py --config path/to/config.json
```

Use `--expect-cuda` only when the task requires GPU runtime evidence. The diagnostic does not download checkpoints or run full model inference.

## Key operating rules

- Never treat a config parse or import check as proof that full LimiX checkpoint inference ran.
- Use no-retrieval configs on CPU. The predictor rejects retrieval when the first pipeline has `retrieval_config.use_retrieval=true` and the device is CPU.
- Prefer explicit local `--data_dir`, `--model_path`, and `--inference_config_path` values. Omitting model/data paths can trigger network downloads into local caches.
- Keep benchmark-scale runs, checkpoint downloads, and Optuna searches behind explicit user approval because they can be long-running, network-dependent, and GPU-memory sensitive.
- When a workflow spans multiple areas, start with the route that owns the immediate user failure: config errors route to configuration/preprocessing; data-root errors route to benchmark CLI; OOM or retrieval parameters route to retrieval optimization; output-shape/API questions route to predictor inference.
