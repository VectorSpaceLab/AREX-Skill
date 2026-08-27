# MOSS bundled CLI/reference commands

## Purpose

Read this when you need a command to validate MOSS prompt, CLI, environment,
serving, or data workflows from this generated skill. The commands here use
bundled helpers, not original checkout demo scripts.

## Safe helpers

| Helper | Purpose | Heavy side effects by default? |
| --- | --- | --- |
| `scripts/check_moss_env.py` | Check imports and optional CUDA against a user-supplied MOSS checkout. | No checkpoint downloads. |
| `sub-skills/model-runtime/scripts/check_model_runtime.py` | Import MOSS model classes, instantiate a tiny config/model, optionally check CUDA. | No checkpoint downloads. |
| `sub-skills/inference/scripts/build_moss_prompt.py` | Build canonical MOSS prompts and model/GPU command suggestions. | No model imports. |
| `sub-skills/inference/scripts/inspect_cli_flags.py` | Validate model/GPU choices and optional Jittor flag concepts. | No model imports. |
| `sub-skills/inference/scripts/run_moss_generation.py` | Dry-run-first generation template; execution is opt-in. | Safe unless `--execute` is passed. |
| `sub-skills/serving/scripts/moss_request_template.py` | Build and validate API request JSON/curl snippets. | Does not contact a server. |
| `sub-skills/serving/scripts/serve_moss_api.py` | Dry-run-first FastAPI service template. | Safe unless `--serve` is passed. |
| `sub-skills/fine-tuning-data/scripts/validate_sft_json.py` | Validate SFT conversation JSON/JSONL schema and markers. | No tokenizer/model/training. |
| `sub-skills/fine-tuning-data/scripts/plan_finetune_command.py` | Plan Accelerate/DeepSpeed SFT command and optional config file. | Writes config only if requested; no training. |

## Common commands

Environment/import check:

```bash
python scripts/check_moss_env.py --repo-root /path/to/MOSS --json
python scripts/check_moss_env.py --repo-root /path/to/MOSS --require-cuda --json
```

Model-runtime check:

```bash
python sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --json
python sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --cuda --json
```

Prompt and command planning:

```bash
python sub-skills/inference/scripts/build_moss_prompt.py --query "Hello MOSS" --json
python sub-skills/inference/scripts/inspect_cli_flags.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0,1 --json
python sub-skills/inference/scripts/run_moss_generation.py --query "Hello MOSS" --json
```

Real generation, only after checkpoint/network/GPU readiness is explicit:

```bash
python sub-skills/inference/scripts/run_moss_generation.py \
  --query "Hello MOSS" \
  --model-name OpenMOSS-Team/moss-moon-003-sft-int4 \
  --gpu 0 \
  --execute
```

Serving request planning:

```bash
python sub-skills/serving/scripts/moss_request_template.py \
  --prompt "Hello MOSS" --max-length 512 --top-p 0.8 --temperature 0.7 --curl
```

Service dry-run/launch:

```bash
python sub-skills/serving/scripts/serve_moss_api.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --json
python sub-skills/serving/scripts/serve_moss_api.py --model-name OpenMOSS-Team/moss-moon-003-sft-int4 --gpu 0 --serve
```

SFT data validation and planning:

```bash
python sub-skills/fine-tuning-data/scripts/validate_sft_json.py sample.json --json
python sub-skills/fine-tuning-data/scripts/validate_sft_json.py plugin_sample.json --expect-plugin --json
python sub-skills/fine-tuning-data/scripts/plan_finetune_command.py \
  --model-name-or-path OpenMOSS-Team/moss-moon-003-base \
  --data-dir /path/to/sft-data \
  --output-dir /path/to/output \
  --log-dir /path/to/logs \
  --write-config /path/to/moss_sft_accelerate.yaml \
  --json
```

## Exit-code expectations

- Helpers return `0` when the planned/check-only workflow is valid.
- Inference model/GPU validators return nonzero for quantized multi-GPU plans.
- SFT schema validation returns nonzero for malformed records.
- `--execute` and `--serve` can fail for network, checkpoint, CUDA, memory, or
  dependency reasons; do not reinterpret those as prompt-format failures.
