# Backend Selection and Batch Inference

## Backend Summary

Set `infer_backend` in an inference YAML or as a CLI override. The documented choices include `huggingface`, `vllm`, `sglang`, and `ktransformers`; this sub-skill owns Hugging Face, vLLM, and SGLang serving decisions.

| Backend | Best for | Requirements | Key limitations |
| --- | --- | --- | --- |
| `huggingface` | Maximum compatibility, CPU/MPS smoke tests, reward-model scores, broad model/template support. | Core Transformers stack and model dependencies. | Usually slower for concurrent generation than specialized serving engines. |
| `vllm` | High-throughput generation and OpenAI-style serving with vLLM engine acceleration. | Optional `vllm` package, compatible GPU/runtime, model support in vLLM. | Does not support `get_scores`; some generation args such as length penalty are ignored or warned. |
| `sglang` | Fast generation through an automatically launched local SGLang HTTP worker. | Optional `sglang[all]`, CUDA/GPU runtime, SGLang-compatible model. | Does not support `get_scores`; supports only `n=1`; startup waits for a local SGLang server. |

If a user asks for model loading, adapter, dtype, quantization, or device placement root causes, route to `model-loading-and-export`. If the question is only which serving backend to choose or how backend choice changes API behavior, stay here.

## Hugging Face Backend

`infer_backend: huggingface` constructs `HuggingfaceEngine`. It supports generation when the finetuning stage is `sft` and score evaluation when the loaded model is non-generating/reward-style.

Use it when:

- The model is small enough for local testing.
- The user needs `/v1/score/evaluation` or `ChatModel.get_scores`.
- Optional vLLM/SGLang packages are missing.
- The user needs the most conservative fallback after specialized backend failures.

A common fallback edit is:

```yaml
infer_backend: huggingface
```

or CLI override:

```bash
llamafactory-cli api CONFIG.yaml infer_backend=huggingface
```

## vLLM Backend

`infer_backend: vllm` constructs `VllmEngine`. If importing vLLM fails, `ChatModel` raises an ImportError advising `pip install vllm` or `--infer_backend huggingface`.

vLLM engine arguments are derived from model args, including:

- `model`: `model_name_or_path`
- `trust_remote_code`
- `download_dir`: cache directory
- `dtype`: `infer_dtype`
- `max_model_len`: `vllm_maxlen`
- `tensor_parallel_size`: detected device count or 1
- `gpu_memory_utilization`: `vllm_gpu_util`
- `enforce_eager`: `vllm_enforce_eager`
- `enable_lora`: true when `adapter_name_or_path` is set
- `max_lora_rank`: `vllm_max_lora_rank`
- plus overrides from `vllm_config` when it is parsed as a dictionary

For multimodal templates, LlamaFactory sets vLLM prompt limits such as up to 4 images, 2 videos, and 2 audios per prompt. For GPTQ models with `infer_dtype: auto`, the backend may force `float16`.

Useful serving launch:

```bash
API_PORT=8000 llamafactory-cli api CONFIG.yaml infer_backend=vllm vllm_enforce_eager=true
```

Use vLLM when the user needs faster concurrent generation and is not using score evaluation. If `/v1/score/evaluation` is required, choose a Hugging Face scorer/reward configuration instead.

## SGLang Backend

`infer_backend: sglang` constructs `SGLangEngine`. If importing SGLang fails, `ChatModel` raises an ImportError advising `pip install sglang[all]` or `--infer_backend huggingface`.

The engine launches a local command equivalent to `python3 -m sglang.launch_server` with model path, dtype, context length, memory fraction, tensor parallel size, download directory, and low log level. When adapters are supplied, it enables one LoRA per batch, sets the configured LoRA backend, passes the first adapter as `lora0`, and disables radix cache.

SGLang request flow:

1. LlamaFactory starts the local SGLang server and waits up to 300 seconds.
2. It sends generation requests to the worker `/generate` endpoint with `input_ids`, sampling params, and `stream: true`.
3. It converts SGLang streamed text into the same `ChatModel` response interface.
4. It terminates the worker process during cleanup.

Use SGLang when the user has a CUDA environment and SGLang-compatible model and wants high-throughput generation. Avoid it for scoring and `n > 1` multi-sample requests.

## Backend Decision Rules

- Start with `huggingface` for minimal direct API validation, score evaluation, CPU/MPS tiny-model tests, or when optional serving packages are unknown.
- Choose `vllm` for OpenAI-compatible API generation throughput when vLLM is installed and the model is supported.
- Choose `sglang` when the target deployment expects SGLang performance and can tolerate a local worker process managed by LlamaFactory.
- Fall back from `vllm` or `sglang` to `huggingface` when the error is an optional package import failure, unsupported worker model, server startup failure, or score endpoint requirement.
- Do not promise exact speedups; actual performance depends on model size, GPU memory, tensor parallelism, dtype, prompt length, and optional backend versions.

## Batch vLLM Prediction Flow

The upstream batch vLLM flow loads a dataset through LlamaFactory's data pipeline, converts examples to token IDs and multimodal payloads, calls vLLM `LLM.generate`, writes JSONL predictions, and optionally computes aggregate metrics.

Important inputs:

- `model_name_or_path`: base model or local model path.
- `adapter_name_or_path`: optional LoRA adapter path.
- `dataset` and `dataset_dir`: LlamaFactory dataset selection.
- `template`: prompt template name.
- `cutoff_len`, `max_new_tokens`, `temperature`, `top_p`, `top_k`, `repetition_penalty`.
- `vllm_config`: JSON object string merged into vLLM engine args.
- `save_name`: prediction JSONL output path.
- `matrix_save_name`: optional metrics JSON output path.
- `pipeline_parallel_size` and `batch_size`: performance/scaling controls.

Output JSONL records follow this shape:

```json
{"prompt": "...", "predict": "...", "label": "..."}
```

When metric output is requested, the flow computes keys such as `predict_bleu-4`, `predict_rouge-1`, `predict_rouge-2`, `predict_rouge-l`, `predict_model_preparation_time`, `predict_runtime`, `predict_samples_per_second`, and `predict_steps_per_second`.

Use bundled `scripts/vllm_batch_infer.py` as a safe wrapper: by default it prints the equivalent command, and it only executes when `--execute` is supplied with model/config arguments.
