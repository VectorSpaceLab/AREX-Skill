# Serving notes

## What the vLLM path does
- The bundled runtime wrapper targets `autoregressive/serve/sample_c2i.py`.
- That script creates a local `LLM` from `autoregressive/serve/llm.py` with `skip_tokenizer_init=True` and a fixed `gpu_memory_utilization` value.
- The model config comes from the local fake JSON files in `autoregressive/serve/fake_json/`.
- The model itself is the class-conditional GPT checkpoint loaded through `autoregressive/serve/model_runner.py`.

## Expected checkpoint forms
`autoregressive/serve/model_runner.py` accepts, in order:
1. a raw FSDP weight object when `--from-fsdp` is set,
2. a checkpoint with a `model` key,
3. a checkpoint with a `state_dict` key,
4. a checkpoint with a `module` key in the sampling path.

Use `--from-fsdp` for raw consolidated FSDP weights; otherwise let the loader pick the keyed checkpoint.

## Supported model configs
The serving JSON files are present for:
- `GPT-B`
- `GPT-L`
- `GPT-XL`
- `GPT-XXL`
- `GPT-3B`

The source model code contains additional class-conditional families, but they are not all wired into the vLLM JSON bundle. Treat unsupported names as a request to extend the serving config, not as a sampling bug.

## Memory and config issues
- If the vLLM loader says the model path or config is invalid, check the local JSON path first.
- If the worker reports cache-block or KV-cache errors, reduce `gpu_memory_utilization` or `max_model_len`.
- If a model fails only when the checkpoint is raw FSDP, confirm `--from-fsdp` and confirm the checkpoint directory really contains the consolidated weights.
- `GPT-3B` uses a head size that the local model patch adapts for vLLM; if a future model family changes head size, expect a serving-side adaptation.

## Reference-only demo
- `app.py` is not a bundled runtime entry point.
- It downloads checkpoints at import time, resolves remote model IDs, and is therefore reference-only for this sub-skill.
- Use the bundled shell wrapper instead of copying the Gradio import pattern into automation.
