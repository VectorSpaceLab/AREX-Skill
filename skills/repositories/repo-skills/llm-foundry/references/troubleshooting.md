# LLM Foundry cross-cutting troubleshooting

Read this when setup, import, CLI routing, optional backends, credentials, or large-run safety affect more than one LLM Foundry workflow. Use the nearest sub-skill troubleshooting reference for workflow-specific data, train, eval, inference, or API details.

## Fast environment check

From the root of this generated skill, run:

```bash
python scripts/check_llmfoundry_environment.py --json
```

This imports `llmfoundry`, checks the console script and registry CLI if available, and reports torch/CUDA visibility. It does not download models or data, train/evaluate, upload artifacts, or touch credentials.

## Install/import health

Expected public setup:

```bash
python -m pip install llm-foundry
python -c "from importlib.metadata import version; print(version('llm-foundry'))"
python -c "import llmfoundry; print(llmfoundry.__version__)"
```

Use an editable install only when working from a checkout or developing extensions:

```bash
python -m pip install -e .
```

Common failures:

- **`No module named llmfoundry` or no distribution metadata:** the active Python does not contain `llm-foundry`; install it in the intended environment and avoid relying on `PYTHONPATH` from a checkout.
- **`pkg_resources` missing or deprecated warning:** this version imports `pkg_resources` through environment logging. If import fails with a very new setuptools, use `python -m pip install 'setuptools<81'` until the package removes that import.
- **Python 3.13 failures:** package metadata supports Python `>=3.10`; compiled ML dependencies are most reliable on Python 3.10-3.12. Prefer Python 3.11/3.12 for new environments.

## CLI route problems

LLM Foundry exposes the `llmfoundry` console script with subcommands:

```bash
llmfoundry --help
llmfoundry train --help
llmfoundry eval --help
llmfoundry registry --help
llmfoundry data_prep --help
```

If the console script is not on `PATH`, use the active environment's scripts directory or reinstall the package. Do not call original checkout scripts as a first resort; the sub-skills provide bundled helpers and public CLI equivalents.

## Optional backend and hardware boundaries

Base install and CPU/API inspection are enough for config work, data preparation, registry inspection, and static linting. Treat these as optional until the user explicitly asks for them and an environment has been prepared:

- FlashAttention (`flash_attn`) and `attn_impl: flash`.
- TransformerEngine (`fc_type: te`, FP8, `te_ln_mlp`).
- MegaBlocks MoE (`mb_moe`, `mb_dmoe`, grouped GEMM).
- FasterTransformer runtime and MPI-enabled PyTorch.
- ROCm, Intel Gaudi, or vendor-specific accelerator forks.
- Multi-node or large multi-GPU training/eval.

If a task only needs CPU-safe API checks, use `attn_impl: torch` and tiny config/model dimensions. If a task needs performance, flash kernels, FSDP/TP, or large-model execution, verify torch/CUDA plus the specific optional package before claiming the backend works.

## Credentials, network, and large artifacts

Stop and confirm before running commands that may:

- Download Hugging Face models/tokenizers/datasets.
- Use private HF, Databricks, MosaicML platform, S3/GCS/OCI/Azure, MLflow, W&B, OpenAI, or custom endpoint credentials.
- Upload model checkpoints, logs, or evaluation outputs.
- Start long training/evaluation/generation or allocate large GPU memory.

Keep secrets in environment variables or platform secret stores, not in YAML examples or generated skill files.

## Which sub-skill should handle the failure?

- Data conversion, JSONL schema, tokenizer concat, MDS remote/local/cache, Databricks table export → [sub-skills/data-preparation/SKILL.md](../sub-skills/data-preparation/SKILL.md).
- Training YAML, Composer launch, callbacks/loggers, optimizer/scheduler, checkpoints, OOM, FSDP/TP, MCLI training jobs → [sub-skills/training-finetuning/SKILL.md](../sub-skills/training-finetuning/SKILL.md).
- ICL task rows, Eval Gauntlet aggregation, eval API wrappers, custom benchmark metrics, max context/batch errors → [sub-skills/evaluation/SKILL.md](../sub-skills/evaluation/SKILL.md).
- HF generation/chat, Composer-to-HF export, ONNX, FasterTransformer, endpoint calls → [sub-skills/inference-conversion/SKILL.md](../sub-skills/inference-conversion/SKILL.md).
- Registry keys, MPT/HF constructor kwargs, optional package imports, MCLI/platform adaptation patterns → [sub-skills/package-apis-configuration/SKILL.md](../sub-skills/package-apis-configuration/SKILL.md).
