# Cross-Cutting Troubleshooting

Use this reference when the failure spans install, import, CLI dispatch, config routing, optional dependencies, hardware, or environment variables. Then route to the nearest sub-skill for workflow-specific fixes.

## Installation Or Import Fails

Symptoms:

- `ModuleNotFoundError` for `torch`, `transformers`, `datasets`, `peft`, `trl`, `gradio`, `fastapi`, `uvicorn`, `sentencepiece`, `tiktoken`, or media packages.
- `pip check` reports missing LlamaFactory requirements.
- `llamafactory-cli help` works only in a source checkout but training/imports fail.

Fix path:

1. Install the base package in a Python version supported by the package metadata, normally Python 3.11 or newer.
2. Verify both metadata and import:

```bash
python - <<'PY'
import importlib.metadata as md
import llamafactory
print(md.version("llamafactory"), llamafactory.__version__)
PY
python -m pip check
llamafactory-cli help
```

3. Install optional backend packages only for the selected workflow; do not install every optional requirements file by default.
4. If the user only needs static config/data checks, use bundled helper scripts that avoid importing LlamaFactory.

## CLI Route Is Wrong

Facts:

- `llamafactory-cli` and `lmf` dispatch through the same launcher.
- Default v0 routes include `train`, `chat`, `api`, `export`, `webchat`, `webui`, `env`, `version`, and `help`.
- `USE_V1=1` switches to the experimental v1 launcher and changes command/config expectations.

Fix path:

- For v0 training, use `llamafactory-cli train CONFIG.yaml`.
- For v0 inference CLI, use `llamafactory-cli chat CONFIG.yaml` or `llamafactory-cli api CONFIG.yaml`.
- For adapter merge/export, use `llamafactory-cli export CONFIG.yaml`.
- For v1, set `USE_V1=1` and route to `sub-skills/v1-experimental/`.

## Config Parses But Behavior Is Unexpected

Common causes:

- YAML/JSON overrides after a config file must use `key=value`, not `--key value`.
- v0 and v1 config fields are mixed.
- Dataset/template errors are being debugged as training errors.
- Export keys are being passed to `train`, or train keys are being passed to `export`.

Route:

- Data/schema/template: `sub-skills/data-and-templates/`
- v0 train/config: `sub-skills/training-and-configs/`
- export/model/adapter/quantization: `sub-skills/model-loading-and-export/`
- v1 config: `sub-skills/v1-experimental/`

## Optional Backend Missing

Common optional surfaces:

- `infer_backend: vllm` requires vLLM and compatible model/runtime support.
- `infer_backend: sglang` requires SGLang packages and service-compatible hardware.
- DeepSpeed, FSDP2, Ray, Megatron-core, KTransformers, FlashAttention, Liger Kernel, Unsloth, bitsandbytes, GPTQ, AWQ, AQLM, HQQ, EETQ, FP8, and NPU paths require their matching optional requirements and hardware.

Fix path:

1. Identify the exact config key or environment variable that enabled the optional path.
2. Check the relevant `requirements/` group from the source evidence or the corresponding sub-skill reference.
3. Prefer a CPU/Hugging Face fallback for inspection or static validation when the user does not need that backend.
4. Do not claim GPU/backend readiness until a tiny backend smoke check passes in the user's environment.

## Environment Variables

Cross-cutting variables include:

- `USE_V1=1`: use experimental v1 launcher.
- `FORCE_TORCHRUN=1`, `NNODES`, `NODE_RANK`, `NPROC_PER_NODE`, `MASTER_ADDR`, `MASTER_PORT`, `MIN_NNODES`, `MAX_NNODES`, `RDZV_ID`, `MAX_RESTARTS`: distributed launch behavior.
- `DISABLE_VERSION_CHECK=1`: skip dependency version checks.
- `RECORD_VRAM=1`: record VRAM usage.
- `LLAMAFACTORY_VERBOSITY`: logging verbosity.
- `USE_MODELSCOPE_HUB=1`, `USE_OPENMIND_HUB=1`: hub selection.
- `API_HOST`, `API_PORT`, `API_KEY`, `API_MODEL_NAME`, `FASTAPI_ROOT_PATH`: API serving behavior.

## Native Verification Limits

A complete native check usually needs PyTorch, Transformers, Datasets, PEFT, TRL, model/tokenizer downloads or local weights, and sometimes GPUs or optional backend packages. If those are unavailable, use static bundled helpers and mark training/inference/native tests as skipped rather than pretending they passed.
