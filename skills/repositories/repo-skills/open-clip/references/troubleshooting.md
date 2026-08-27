# Cross-Cutting Troubleshooting

## Import Or Install Fails

Symptoms:
- `ModuleNotFoundError: open_clip` or `ModuleNotFoundError: open_clip_train`.
- Optional modules fail, such as `webdataset`, `transformers`, `torchaudio`, `torchlibrosa`, `datasets`, or `tiktoken`.

Actions:
1. Run `python scripts/check_open_clip_env.py` to separate base import failures from optional training/audio/NaFlex issues.
2. Install the smallest needed extra: base `open_clip_torch` for inference, `[training]` for `open_clip_train` data/training workflows, `[audio]` for CLAP audio workflows.
3. If model configs or pretrained registries look stale, compare the package version and provenance snapshot.

## Downloads, Caches, And Credentials

Symptoms:
- Hugging Face Hub errors, cache permission failures, rate limits, missing model files, or dataset download prompts.
- A smoke helper refuses a `pretrained` or `hf-hub:` path.

Actions:
1. Prefer no-download helpers first, such as model creation with `pretrained=None` or argument-report scripts.
2. Only enable download-prone pretrained or dataset workflows when the user explicitly authorizes network/cache access.
3. Use a public cache location chosen by the user; do not hard-code machine-specific cache paths into final code or docs.
4. If Hugging Face export is requested, route to `sub-skills/evaluation-conversion/SKILL.md` and confirm credentials before upload-like operations.

## Torch, CUDA, And Precision

Symptoms:
- CUDA requested but unavailable, CPU fp16 problems, CUDA OOM, unsupported kernel, or inconsistent GPU behavior.
- Training behaves differently after upgrading because default precision is `amp_bf16`.

Actions:
1. Check torch backend facts with `python scripts/check_open_clip_env.py --show-torch`.
2. Use CPU `fp32` for deterministic smoke checks.
3. Use `amp_bf16` or GPU precision modes only when torch and the hardware backend support them.
4. For training compile/FSDP constraints, route to `sub-skills/training/SKILL.md`.

## Model Family Mismatch

Symptoms:
- A user tries image zero-shot on CLAP audio models.
- A user tries CLIP-style cosine text/image embeddings with GenLIP or GenLAP.
- A checkpoint loads with many missing/unexpected keys.

Actions:
1. Route image/text CLIP and CoCa loading to `sub-skills/model-inference/SKILL.md`.
2. Route CLAP audio zero-shot to `sub-skills/audio-clap/SKILL.md`.
3. Route GenLIP/GenLAP generative scoring to `sub-skills/naflex-generative/SKILL.md`.
4. Route generic checkpoint prefix, EMA, or key-shape diagnosis to `sub-skills/evaluation-conversion/SKILL.md`.

## Data And Parser Confusion

Symptoms:
- CSV training cannot find `filepath` or `title` columns.
- WebDataset training complains about sample counts.
- Batch consumers expect tuples but receive dictionaries.

Actions:
1. Use `sub-skills/training/scripts/validate_csv_dataset.py` for CSV/TSV structure and image path checks.
2. Use `sub-skills/training/scripts/training_arg_report.py -- [args...]` to inspect parser defaults before launching training.
3. Remember that task-era loaders emit dict batches, such as `image`/`text`, `audio`/`text`, and optional `text_valid`.

## Stale Skill Or Version Drift

Symptoms:
- Parser flags, public APIs, model config names, or docs differ from this skill.
- `open_clip.__version__` or the current commit differs from `references/repo-provenance.md`.

Actions:
1. Treat the skill as potentially stale.
2. Run `refresh-repo-skill` against the current repository before relying on detailed API or troubleshooting claims.
3. Preserve runtime/verification separation when refreshing: public skill content stays under the runtime skill directory; verification outputs stay outside the runtime skill.
