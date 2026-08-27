# API serving workflows

## Non-vLLM FastAPI server

Primary script: `scripts/openai_server_demo/openai_api_server.py`

Useful launch arguments:

| Flag | Meaning |
| --- | --- |
| `--base_model` | HF-format base or merged model path |
| `--lora_model` | Optional PEFT adapter path or Hub id |
| `--tokenizer_path` | Optional tokenizer path; defaults to LoRA path, then base model path |
| `--gpus` | Comma-separated CUDA device ids |
| `--only_cpu` | Force CPU inference; quantized loading is disabled in this mode |
| `--load_in_8bit`, `--load_in_4bit` | Quantized loading paths |
| `--use_ntk`, `--alpha` | Long-context NTK patch controls |
| `--use_flash_attention_2` | Optional attention acceleration |

The non-vLLM server loads the model through Transformers and PEFT, builds Alpaca-2 prompt templates, and exposes OpenAI-style request models.

## Request families

| Endpoint family | Request model | Notes |
| --- | --- | --- |
| Completion | `CompletionRequest` | Prompt-based text completion with decoding controls |
| Chat completion | `ChatCompletionRequest` | List of role/content messages or a string-like prompt payload |
| Model listing | vLLM variant only has explicit model list support | Use model name consistently across requests |

Common request fields include `temperature`, `top_p`, `top_k`, `n`, `max_tokens`, `num_beams`, `stream`, `repetition_penalty`, `stop`, and `user`.

## Optional vLLM server

Primary script: `scripts/openai_server_demo/openai_api_server_vllm.py`

Treat this path as optional because it requires the vLLM and FastChat dependency stack. In the repo snapshot, the vLLM implementation registers Chinese-LLaMA-Alpaca conversation templates and routes completions through vLLM sampling parameters.

Important limitations:

- no CPU serving
- no LoRA model loading in this branch
- no 4-bit or 8-bit quantized branch through the bundled vLLM server
- stricter served-model-name and request model checks

## Response shape

The protocol helper files define Pydantic response models for completion and chat completion choices. Streaming responses emit incremental chunks rather than a single final response body.
