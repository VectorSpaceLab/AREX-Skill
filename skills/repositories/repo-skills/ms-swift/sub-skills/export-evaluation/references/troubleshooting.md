# Export and Evaluation Troubleshooting

## `swift eval --help` Fails Before Printing Help

Likely cause: EvalScope is not installed. The eval pipeline imports EvalScope at import time, so even help can fail in a minimal `ms-swift` environment.

Fix:

```bash
pip install ms-swift[eval] -U
swift eval --help
```

If using multimodal or OpenCompass backends, additional backend dependencies may still be needed. For a quick smoke test, use `--eval_backend Native --eval_limit 1` and a small text benchmark before trying heavier backends.

## Dataset Name Is Rejected

Symptoms: `eval_dataset: <name> is not supported` or backend-specific dataset list errors.

Checklist:

- Confirm the dataset belongs to the selected `--eval_backend`.
- Use `Native` for `general_mcq` and `general_qa`; custom datasets are not valid for `OpenCompass` or `VLMEvalKit`.
- Check spelling and case. ms-swift maps names case-insensitively to the backend registry, but punctuation and aliases still matter.
- For `OpenCompass`, avoid an unrelated local `data` directory when `--local_dataset true` is enabled; the backend may need to create or symlink a `data` folder.

## Custom MCQ or QA Data Fails

MCQ checklist:

- Folder contains `{subset}_val.csv`; `{subset}_dev.csv` is optional.
- Header includes `question`, option columns such as `A,B,C,D`, and `answer`.
- Each row has at least two non-empty options.
- `answer` is a present option letter, not the option text.
- Command uses `--eval_dataset general_mcq` and `--eval_backend Native`.

QA checklist:

- Folder contains `{subset}.jsonl`.
- Every non-empty line is JSON object with non-empty string `query` and `response`.
- Command uses `--eval_dataset general_qa` and `--eval_backend Native`.

Use:

```bash
python scripts/validate_eval_dataset.py mcq ./mcq --subset example
python scripts/validate_eval_dataset.py qa ./qa --subset example
```

## Hub Push Fails

Common causes:

- Missing or invalid `--hub_token`.
- Token lacks write access to `--hub_model_id` namespace.
- Target should be Hugging Face but `--use_hf true` was omitted; default target is ModelScope.
- Private repository creation requires `--hub_private_repo true` on first push.
- A full model directory was intended but `--adapters` points to an adapter-only checkpoint for a non-push operation.

Security rules:

- Do not put tokens in committed files or shared command transcripts.
- Prefer shell environment variables such as `$HF_TOKEN` or `$MODELSCOPE_TOKEN`.
- Redact command logs before sharing support information.

## AWQ/GPTQ/GPTQ v2/BNB Dependency Errors

Method-specific installs:

```bash
pip install autoawq -U
pip install auto_gptq optimum -U
pip install gptqmodel optimum -U
pip install bitsandbytes -U
```

Decision hints:

- AWQ and GPTQ need calibration data through `--dataset`; ms-swift raises an error if no dataset is supplied.
- AWQ and GPTQ need `--quant_bits`; FP8 does not.
- BNB supports `--quant_bits 4` and `--quant_bits 8`; unsupported bit sizes fail validation.
- AutoAWQ and AutoGPTQ are sensitive to CUDA, torch, and Python versions. If torch conflicts appear, resolve them deliberately rather than force-installing broad packages.
- `--quant_batch_size -1` is normalized to no explicit batch size; use this only when the backend supports automatic sizing.

## Merge, Adapter, and Model Path Confusion

Use these rules before running export:

- `--adapters` means LoRA-like adapter checkpoint for merge/export workflows.
- `--model` means base model ID, full model directory, merged output directory, or quantized model directory.
- For pure hub push, `--model <checkpoint-dir>` and `--adapters <checkpoint-dir>` can both point to the artifact to push.
- For merging, prefer `--adapters <swift-checkpoint>` because the checkpoint metadata can recover model/template settings.
- For quantizing a trained LoRA result, merge first, then quantize the merged model.

## QLoRA Merge Is Not a Safe Plan

If a user wants vLLM/SGLang/LMDeploy acceleration from a QLoRA-trained adapter, warn that QLoRA-trained models cannot be merged into full weights in the same way as ordinary LoRA. Recommend one of these plans:

- Train with standard LoRA or full-parameter fine-tuning, merge with `--merge_lora true`, then export AWQ/GPTQ/BNB/FP8.
- Keep the QLoRA adapter for transformer-based inference paths that support loading it, without promising merged full weights.
- If the base model is already AWQ/GPTQ and the task is additional QLoRA training, do not add unrelated export quantization flags during training.

## Output Directory Already Exists

`ExportArguments` derives an output suffix when `--output_dir` is omitted: merged, quantized, cached dataset, Ollama, and conversion paths get distinct suffixes. If the directory exists:

- Pick a new `--output_dir` for reproducible artifacts.
- Use `--exist_ok true` only when overwrite behavior is intentional.
- For merge specifically, an existing merged directory may cause saving to be skipped unless replacement behavior is requested by the calling API.

## Eval URL Confusion

`--eval_url` should usually be the service base URL, for example `http://127.0.0.1:8000/v1`. If a user passes a URL ending in `/chat/completions`, ms-swift strips that suffix internally. For `OpenCompass` and `VLMEvalKit`, ms-swift adds `/chat/completions` when building the backend task config.

If the eval task cannot connect:

- Confirm the service is already running.
- Confirm API key behavior with `--api_key` if the service requires auth.
- Lower `--eval_num_proc` when the service is overloaded.
- Start with `--eval_limit 1` and one dataset before scaling.
