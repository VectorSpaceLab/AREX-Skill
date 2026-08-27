# Pipeline Troubleshooting

Use this guide for offline text inference through `lmdeploy.pipeline`, `Pipeline`, and `lmdeploy chat`.

## Quick Triage

Run no-model checks first:

```bash
python sub-skills/pipeline-inference/scripts/inspect_pipeline_config.py --include-cli
lmdeploy chat --help
```

Then collect the user’s model path/repo id, backend (`turbomind`, `pytorch`, or auto), config values, prompt shape, exact error, accelerator type/count, and whether model downloads or `trust_remote_code` are allowed.

## OOM During Pipeline Creation or Inference

Symptoms:

- `CUDA runtime error: out of memory`.
- TurboMind allocator errors mentioning KV cache.
- Process exits during prefill or after raising `session_len`, batch size, or `max_new_tokens`.

First recovery:

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline

backend_config = TurbomindEngineConfig(
    cache_max_entry_count=0.2,
    session_len=2048,
    max_batch_size=1,
)
gen_config = GenerationConfig(max_new_tokens=64)

with pipeline("org/model-or-local-path", backend_config=backend_config) as pipe:
    print(pipe("Short test", gen_config=gen_config).text)
```

CLI recovery:

```bash
lmdeploy chat org/model-or-local-path --cache-max-entry-count 0.2 --session-len 2048
```

Then tune gradually:

- Lower `cache_max_entry_count` first; modern LMDeploy interprets the float as a fraction of free GPU memory for KV cache.
- Lower `session_len`, `max_batch_size`, `max_new_tokens`, and prompt length.
- Avoid `output_logits="all"` and `output_last_hidden_state="all"` unless required.
- Use a smaller model, quantized model, or more GPUs only after config reductions fail.
- For `get_ppl`, shorten token sequences; documentation warns long `input_ids` can OOM.

## PyTorch Tensor Parallel Multiprocessing Error

Symptom:

```text
RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase
```

Usually occurs with PyTorch backend and `tp > 1` when pipeline creation runs at module import time.

Fix:

```python
from lmdeploy import PytorchEngineConfig, pipeline


def main():
    backend_config = PytorchEngineConfig(tp=2, session_len=4096)
    with pipeline("org/model-or-local-path", backend_config=backend_config) as pipe:
        print(pipe("Hello").text)


if __name__ == "__main__":
    main()
```

Also avoid creating global `Pipeline` objects in modules imported by worker processes.

## Missing `_turbomind`

Symptoms:

- `ModuleNotFoundError: No module named '_turbomind'`.
- Import or pipeline construction fails only for TurboMind-backed commands.

Recoveries:

- Install a precompiled LMDeploy package that includes TurboMind for the target platform, commonly the package extras recommended by LMDeploy documentation.
- Do not run TurboMind commands from inside a source checkout that shadows the installed package unless the extension has been built and linked for that checkout.
- If only PyTorch backend is needed and installed dependencies support it, try `PytorchEngineConfig(...)` or `lmdeploy chat ... --backend pytorch`.
- Check Python version/environment consistency; a compiled extension built for one Python cannot be imported by another.

Route build or extension-linking work to `backend-extension`.

## Chat Template Mismatch

Symptoms:

- Model prints role markers such as `<|im_start|>user`.
- Model repeats the prompt or ignores the system instruction.
- A LoRA adapter produces output in the wrong language/style.
- Offline output differs sharply from the model’s expected Hugging Face chat behavior.

Recoveries:

- Try `ChatTemplateConfig(model_name="hf", model_path=model_path)` for instruct models with a reliable tokenizer template.
- Load a JSON template with `ChatTemplateConfig.from_json(...)` or `lmdeploy chat --chat-template template.json`.
- Register a Python `BaseChatTemplate` subclass before constructing the pipeline.
- Set `log_level="INFO"` and compare rendered prompts with the expected tokenizer chat template.
- Add template `stop_words` for assistant/user boundary tokens.

See `references/chat-templates.md` for complete patterns.

## Invalid Stop Words, Bad Words, or Token IDs

Symptoms:

- Assertion error that `stop_words` must be a list of strings.
- Unexpected early stopping or no stopping.
- Stop tokens appear in output unexpectedly.

Recoveries:

- Pass `stop_words=["..."]` and `bad_words=["..."]`, not a single string.
- Pass integer ids in `stop_token_ids` / `bad_token_ids`.
- Let `GenerationConfig.convert_stop_bad_words_to_ids(tokenizer)` merge string and token-id stop conditions when you have a tokenizer object.
- Keep `include_stop_str_in_output=False` unless the caller needs the stop text retained.
- For chat boundary tokens, prefer fixing the chat template so stop words and prompt delimiters align.

## GenerationConfig Validation Errors

Common causes:

- `top_p` outside `[0, 1]`.
- `top_k < 0`.
- `temperature` outside `[0, 2]`.
- `min_p` outside `[0, 1]`.
- `n <= 0`; current engines only support `n=1` in practical use.
- Invalid `cache_max_entry_count`, `tp`, `block_size`, `quant_policy`, or `device_type` in backend configs.

Recovery:

- Instantiate config objects in a no-model unit test before running the model.
- Use the inspection script to print installed defaults.
- Validate user input before constructing `GenerationConfig` or backend configs.

## Prompt, Batch, or Session Shape Errors

Symptoms:

- `ValueError` about prompts and sessions having different lengths.
- `ValueError` about `gen_config` length differing from prompt count.
- One message batch treated as a single prompt or vice versa.

Recoveries:

- Use `str` for one prompt, `list[str]` for a batch.
- Use `list[dict]` for one OpenAI-style conversation.
- Use `list[list[dict]]` for a batch of conversations.
- If passing `sessions`, provide one session per prompt.
- If passing a list of `GenerationConfig`, provide one config per prompt.
- Prefer `Pipeline.chat` for multi-turn sessions unless low-level streaming control is necessary.

## Model Download and `trust_remote_code` Risks

Symptoms:

- The code unexpectedly tries to access a model hub.
- Tokenizer/model loading asks for remote custom code.
- Auth or network errors occur before inference.

Recoveries:

- Use a local model path for offline/hardened workflows.
- Set `download_dir` and `revision` in backend configs when remote resolution is intentional.
- Keep `trust_remote_code=False` unless the model requires it and the user accepts remote-code execution risk.
- Confirm credentials and network policy before recommending repo ids that require authentication.

## CLI Help Works but `lmdeploy chat` Fails

Check:

- Is the selected backend installed? Try `--backend pytorch` if TurboMind extension is unavailable.
- Is the model too large for available memory? Lower `--cache-max-entry-count`, `--session-len`, and generation options.
- Is the chat template wrong? Add `--chat-template <name-or-json-file>`.
- Is prefix caching enabled? Interactive chat refuses prefix caching.
- Are LoRA adapters in valid CLI format? One adapter may be a path; multiple adapters must be `name=path` pairs.

## Resource Leaks or Hanging Scripts

Symptoms:

- Process stays alive after inference.
- Tests hang after creating a pipeline.
- Repeated notebook runs accumulate memory.

Recoveries:

- Use `with pipeline(...) as pipe:`.
- Or call `pipe.close()` in `finally`.
- In tests, delete the pipeline and clear accelerator cache only after `close()`.
- Avoid module-level global pipeline instances.

## Routing Notes

- If the failure is in API server startup, proxying, OpenAI clients, or HTTP request payloads, route to `serving-apis`.
- If the failure is image/video loading or multimodal placeholder handling, route to `vision-language`.
- If the failure happens while creating quantized weights, route to `quantization`.
- If the failure requires editing model patches, kernels, or backend internals, route to `backend-extension`.
