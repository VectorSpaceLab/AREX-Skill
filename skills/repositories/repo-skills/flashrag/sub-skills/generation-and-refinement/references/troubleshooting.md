# Troubleshooting Generation and Refinement

## Fast Preflight

Run the bundled static checker before loading large models or calling APIs:

```bash
python skills/flashrag/sub-skills/generation-and-refinement/scripts/inspect_generation_config.py my_config.yaml
```

The checker parses YAML or JSON and reports missing keys, backend mismatch risks, credential placeholders, dependency hints, and refiner/judger shape issues. It does not import FlashRAG, load models, download tokenizers, or call external APIs.

## Generator Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: transformers` or `torch` | HF/FastChat/refiner dependency missing | Install the FlashRAG runtime dependencies plus the backend-specific package set for the chosen component. |
| `ModuleNotFoundError: vllm` | `framework: vllm` without vLLM installed | Install vLLM in a compatible CUDA/PyTorch environment, or switch `framework` to `hf` for local debugging. |
| `ModuleNotFoundError: openai` or `tiktoken` | OpenAI backend dependencies missing | Install `openai` and `tiktoken`; verify the config uses `framework: openai`. |
| OpenAI authentication failure | Missing or placeholder `openai_setting.api_key`, missing `OPENAI_API_KEY`, or wrong Azure settings | Use an environment variable or secret manager; for Azure include the correct endpoint/version fields for the OpenAI client. |
| Model path file errors before generation | `generator_model_path` is unset, points to a non-model directory, or only `generator_model` was set without `model2path` | Set `model2path` or explicit `generator_model_path`; confirm the path contains model config files for local models. |
| Bad or empty chat answers | Tokenizer/template mismatch | Use `PromptTemplate`, confirm tokenizer `apply_chat_template` support, or use FastChat for models whose conversation format is FastChat-supported. |
| `SamplingParams` validation errors | HF/OpenAI-only parameters passed to vLLM | Trim `generation_params` to vLLM-supported keys and prefer `max_tokens` for vLLM. |
| HF `generate` argument errors | vLLM/OpenAI-only parameters passed to Transformers | Trim `generation_params` to Transformers-supported keys and prefer `max_new_tokens`. |
| Unexpected truncation warning | Prompt tokens exceed `generator_max_input_len` | Increase the config limit if the backend/model supports it, reduce retrieved context, or add a refiner before prompt construction. |
| Stop words not behaving identically across backends | HF uses custom stopping criteria; OpenAI may not include stop strings; vLLM may include stop strings when configured | Treat stop behavior as backend-specific and test the exact backend. |

## Multimodal Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Multimodal model loads as text-only or crashes reading config | `generator_model_path` does not point to the intended VLM config | Set a valid local path or model id and verify the config contains vision-related fields. |
| `ModuleNotFoundError: qwen_vl_utils` | Qwen2-VL support package missing | Install the Qwen-VL utility package required by the model family. |
| Image processing errors | Image path/URL/PIL object not supported by the selected engine or missing PIL/requests/torchvision-style dependencies | Convert input to the expected message content format and install image dependencies for that model family. |
| PromptTemplate output rejected by VLM | Multimodal generators expect message blocks, not FlashRAG text prompts | Build `List[List[dict]]` inputs with `content` entries containing `image` and `text`. |

## Refiner Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AttributeError` for `retrieval_result` | Refiner is called before retrieval results are attached to the dataset | Populate `Dataset` items with `retrieval_result` or use a prompt-based LLMLingua flow with `refiner_input_prompt_flag: true`. |
| `AttributeError` for `prompt` | `LLMLinguaRefiner` has `refiner_input_prompt_flag: true` but items lack `prompt` | Add prompt strings to each item or set the flag to false and provide retrieval results. |
| LLMLingua import/model errors | LLMLingua compressor dependencies or model path missing | Install the compressor dependencies and point `refiner_model_path` at a usable perplexity model. |
| Selective Context import/model errors | Selective Context dependencies or GPT-2-style model path missing | Install required packages and set `refiner_model_path` to a compatible GPT-2 model. |
| RECOMP refiner selects unexpected class | `refiner_name` and model architecture disagree | Use explicit `refiner_name`, set a compatible `refiner_model_path`, and verify whether the model is T5/BART or embedding-like. |
| Output is too short or too long | Compression ratio or top-k/output-length settings are misaligned | Tune `llmlingua_config.rate`, `sc_config.reduce_ratio`, `refiner_topk`, or seq2seq output length settings. |

## Judger Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: No implementation!` | `judger_name` does not contain `skr` or `adaptive` | Use a supported judger name or implement a new judger class and factory branch. |
| Key error in `judger_config` | Missing `model_path`, `training_data_path`, or other required fields | Match the SKR or Adaptive config shape in `refiner-and-judger.md`. |
| SKR returns poor decisions | Training data judgement labels or domain do not match target questions | Use representative training data with `ir_better` and `ir_worse` labels. |
| Adaptive labels are hard to interpret | The classifier returns method-specific classes rather than booleans | Map labels to the retrieval policy required by the surrounding pipeline. |

## Credential Hygiene

- Keep API keys out of YAML committed to source control and out of generated skill content.
- Prefer `openai_setting.api_key: null` with `OPENAI_API_KEY` in the environment.
- In examples, use placeholders such as `${OPENAI_API_KEY}` or `<OPENAI_API_KEY>` and state that they must be replaced securely.

## Dependency Hints

- Text HF/FastChat generation: `torch`, `transformers`, `tqdm`.
- OpenAI backend: `openai`, `tiktoken`.
- vLLM backend: `vllm` plus a compatible PyTorch/CUDA stack.
- Multimodal Qwen2-VL: `qwen_vl_utils` plus image processing dependencies.
- Refiners: model-specific HF dependencies, FlashRAG retriever encoder utilities for extractive refinement, LLMLingua or Selective Context dependencies for those compressors.
- Judgers: `faiss`, `torch`, `transformers`, and model/data files matching the selected judger.
