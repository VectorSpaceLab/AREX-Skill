# Evaluation and WebUI notes

## Evaluation workflow

`dataflow eval` is a template-driven evaluation harness, not a dry-run.

### Template bootstrap

`dataflow eval init` copies two files into the current working directory:

- `eval_api.py`
- `eval_local.py`

If either file already exists, the command asks before overwriting.

### Template contract

Both templates are expected to export `get_evaluator_config()`, and the returned dictionary usually contains:

- `JUDGE_MODEL_CONFIG`
- `TARGET_MODELS`
- `BENCH_CONFIG`
- `EVAL_CONFIG`
- `EVALUATOR_RUN_CONFIG`
- `create_judge_serving`
- `create_evaluator`
- `create_storage`

The evaluator run uses the model / bench configuration to build a judge serving, create storage, run the evaluator, and write reports.

### `eval api`

- Uses an API-backed judge model.
- Typically routes to `APILLMServing_request` for the judge.
- Best when you already have a remote OpenAI-style endpoint and `DF_API_KEY` is set.

### `eval local`

- Uses a local judge model.
- The stock template builds a `LocalModelLLMServing_vllm` judge.
- Requires a local model path or a downloadable Hugging Face model plus vLLM.

### High-level caution

- `eval api` can call remote services.
- `eval local` can load large local models and use GPU memory.
- Both commands write cache and result files.

## Chat routing

`dataflow chat` resolves the model in this order:

1. explicit `--model`
2. adapter files in the current directory
3. latest cached adapter in `<cache>/.cache/saves`
4. base model fallback through `llamafactory-cli chat`

If the selected path is a fine-tuned adapter, the wrapper launches `llamafactory-cli chat --model_name_or_path <base> --adapter_name_or_path <adapter>`.

If the selected path is a base model, the wrapper falls back to plain `llamafactory-cli chat`.

## WebUI side effects

`dataflow webui` has significant side effects:

- it may fetch the latest `OpenDCAI/DataFlow-WebUI` release from GitHub
- it installs backend requirements into the current Python environment
- it launches `uvicorn app.main:app --reload`
- it attempts to open a browser when the server becomes reachable

Useful options:

- `--zip-path PATH`: use a local WebUI release zip
- `--webui-path PATH`: use an extracted backend directory or a directory containing `backend/`
- `--host`: default `0.0.0.0`
- `--port`: default `8000`

## What to avoid

- Do not treat `webui` as a pure help command; it downloads, installs, and starts a service.
- Do not use `chat` as a generic model loader; it is a routing layer with adapter detection and external CLI fallback.
- Do not use `eval` as a quick lint check; it is a model execution workflow.
