---
name: benchmark-cli
description: "Use LimiX benchmark-style classification and regression CLI
  commands with safe local dataset and checkpoint handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# benchmark-cli

Use this sub-skill when a task asks for LimiX benchmark-style CLI inference over one or more local tabular dataset folders, result CSV collection, or dataset-layout validation before running the classification/regression benchmark scripts.

## Start here

1. Validate the dataset root before model inference:
   ```bash
   python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py DATASET_ROOT --task classification
   python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py DATASET_ROOT --task regression
   ```
2. Prefer local inputs: pass both `--data_dir` and `--model_path`. Omitting either can trigger network downloads into `./cache`.
3. Choose an explicit config JSON path instead of relying on missing default config filenames.
4. Treat full checkpoint CLI inference as GPU/CUDA-sensitive: the benchmark scripts guard on CUDA availability before they process workloads, and full LimiX checkpoint inference needs a local LimiX checkpoint. Do not claim a benchmark CLI was run unless it actually completed.

## Reference map

- `references/cli-reference.md`: flag meanings, safe local command templates, DDP launch shapes, output files, and metrics.
- `references/dataset-layout.md`: expected dataset-folder schema, target-column placement, train/test behavior, dtype/category handling, and validator usage.
- `references/troubleshooting.md`: GPU guard, auto-download/network failures, class-count and row-count skips, data-shape errors, DDP notes, and result-path confusion.

## Routing boundaries

- For direct `LimiXPredictor` Python API usage, route to `../predictor-inference/SKILL.md`.
- For inference config schema details, config generation, or preprocessing-pipeline edits, route to `../configuration-preprocessing/SKILL.md`.
- For retrieval tuning/search-space semantics beyond the CLI flag surface, route to `../retrieval-optimization/SKILL.md`.
- Do not run heavyweight benchmark CLIs as a validation shortcut. Use the bundled dataset validator and provide command recipes unless the user explicitly authorizes full inference with local data, a local checkpoint, and a ready CUDA/GPU environment.
