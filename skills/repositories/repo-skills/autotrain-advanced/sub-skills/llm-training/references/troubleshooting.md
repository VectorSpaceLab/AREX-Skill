# LLM troubleshooting

## CLI validation errors

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `Project name must be specified` | `--train` was used without `--project-name` | Add a short project name. |
| `Data path must be specified` | `--train` was used without `--data-path` | Provide a local path or Hub dataset id. |
| `Model must be specified` | `--train` was used without `--model` | Provide the base model id/path. |
| Username/token errors with Hub or hosted backends | `--push-to-hub`, `spaces-*`, or `ep-*` needs credentials | Add `--username` and `--token` or use `local`. |
| `Deploy is not implemented yet` / `Inference is not implemented yet` | Those branches are stubs in this checkout | Do not use `--deploy` or `--inference`; use training only. |

## Data and column errors

- SFT/default runs need a valid `text_column`.
- DPO/ORPO/reward-style runs normally need chosen, rejected, and prompt columns mapped via `text_column`, `rejected_text_column`, and `prompt_text_column`.
- If a YAML config uses `${HF_USERNAME}` or `${HF_TOKEN}`, ensure those environment variables are set before parsing/running.
- For local files, validate columns before launch with the text/tabular validator.

## PEFT, quantization, and accelerator issues

- `quantization: int4` or `int8` commonly depends on a compatible bitsandbytes/CUDA stack.
- `use_flash_attention_2` requires hardware, package, and model support; disable it first when debugging unexplained import/runtime failures.
- `unsloth: true` requires unsloth-compatible packages and models; turn it off when reproducing a minimal baseline.
- `target_modules: all-linear` is a common default, but some architectures need explicit target module names.

## Backend issues

- Hosted backends require Hub push because the job needs an artifact/source of truth that the backend can access.
- If a hosted backend fails before job creation, switch to `local` to validate parser/data logic first.
- If the task is app/API driven, use `app-backends` to inspect auth, jobs, and backend-specific logs.

## Minimal recovery checklist

```bash
python skills/disco/autotrain-advanced/scripts/check_install.py
python skills/disco/autotrain-advanced/scripts/check_backends.py
python skills/disco/autotrain-advanced/scripts/inspect_cli.py llm --help
python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/llm.yml
```

Then validate local data columns if applicable and reduce acceleration knobs before rerunning.
