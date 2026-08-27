---
name: configuration-preprocessing
description: "Inspect, choose, generate, and debug LimiX inference configs and
  preprocessing transforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LimiX configuration and preprocessing router

Use this sub-skill when the task is to choose, validate, generate, or debug a LimiX inference configuration JSON or the preprocessing blocks that a config enables.

Do **not** use this sub-skill to run the model end to end. Full checkpoint inference needs a local LimiX checkpoint and may require CUDA/GPU; this sub-skill only covers configuration and preprocessing decisions.

## Route by intent

- Need to call `LimiXPredictor`, prepare `x_train`/`y_train`/`x_test`, inspect outputs, or use missing-value imputation? Load `../predictor-inference/SKILL.md`.
- Need to run the benchmark-style classification/regression CLI over dataset directories? Load `../benchmark-cli/SKILL.md`.
- Need retrieval search, Optuna tuning, attention-map semantics, or retrieval-parameter trade-offs? Load `../retrieval-optimization/SKILL.md`.
- Need to inspect whether a JSON config is valid, CPU-safe, retrieval-enabled, MVI-compatible, or likely to fail in preprocessing? Continue here.

## Operating checklist

1. Pick the nearest catalog config from `references/config-catalog.md` by task, model size, retrieval use, and MVI need.
2. For CPU or low-memory work, prefer non-retrieval configs; LimiX rejects retrieval configs on CPU and retrieval inference can be GPU-memory heavy.
3. Validate user-supplied JSON with `scripts/inspect_config.py` before using it in a predictor or benchmark command.
4. If no config file exists, generate a safe no-retrieval baseline with `scripts/generate_noretrieval_config.py`, then inspect it.
5. When a preprocessing failure mentions constant/all-NaN features, category encoding, power transforms, one-hot size, KDI, Hyperopt, or malformed config keys, use `references/troubleshooting.md`.

## Bundled references and scripts

- `references/config-catalog.md`: observed config matrix, config-list schema, helper-generated configs, and CPU/retrieval caveats.
- `references/preprocessing-reference.md`: transform order, class behavior, key options, data implications, and failure modes.
- `references/troubleshooting.md`: actionable fixes for malformed configs and preprocessing/runtime errors.
- `scripts/inspect_config.py`: standalone JSON validator and config summarizer.
- `scripts/generate_noretrieval_config.py`: standalone no-retrieval config generator.
