# Backend Reference

LM Evaluation Harness registers model backends by string aliases. Importing `lm_eval.models` populates lazy registry entries, but importing a concrete backend class may still fail until its optional dependency extra is installed.

## Install Only What You Need

The distribution is `lm_eval` and the package version inspected for this skill was `0.4.13.dev0`. Python `>=3.10` is required. The base install provides the framework, CLI, task system, registry, and APIs, but not all model engines.

| Extra | Installs | Use for |
| --- | --- | --- |
| `api` | `requests`, `aiohttp`, `tenacity`, `tqdm`, `tiktoken` | OpenAI-compatible completions/chat, commercial APIs, self-hosted HTTP APIs |
| `hf` | `transformers>=4.1`, `torch>=1.8`, `accelerate>=0.26.0`, `peft>=0.2.0` | `hf`, `huggingface`, `hf-auto`, PEFT/delta/GGUF through Transformers |
| `vllm` | `vllm>=0.18` | `vllm`, `vllm-vlm` |
| `litellm` | `litellm>=1.60,<1.85`, plus API transport packages | `litellm`, `litellm-chat`, `litellm-chat-completions` |
| `gptq` | `auto-gptq[triton]>=0.6.0` | Hugging Face AutoGPTQ model args |
| `gptqmodel` | `gptqmodel>=1.0.9` | Hugging Face GPTQModel model args |
| `optimum` | `optimum[openvino]` | `openvino` |
| `ipex` | `optimum-intel` | `ipex` |
| `habana` | `optimum-habana` | `habana` |
| `ibm_watsonx_ai` | `ibm_watsonx_ai>=1.1.22`, `python-dotenv` | `watsonx_llm` |
| `winml` | Not declared in metadata; README documents Windows AI packages separately | `winml` |

Install examples:

```bash
pip install "lm_eval[hf]"
pip install "lm_eval[vllm]"
pip install "lm_eval[api]"
pip install "lm_eval[hf,api]"
```

Do not install all extras by default: some groups conflict or require specific hardware/toolchains. For example, `gptq` conflicts with `vllm` in project metadata, and low-level CUDA or Windows ML packages may require platform-specific setup.

## Built-In Backend Aliases

Common registry aliases after importing `lm_eval.models` include:

| Alias | Backing class family | Typical extra | Request types / caveats |
| --- | --- | --- | --- |
| `hf`, `huggingface`, `hf-auto` | Hugging Face `HFLM` | `hf` | `generate_until`, `loglikelihood`, `loglikelihood_rolling`; supports causal and seq2seq models |
| `vllm` | vLLM causal LM | `vllm` | Fast local inference; supports generation and loglikelihood; `think_end_token` must be a string |
| `sglang` | SGLang local engine | separate SGLang install | Efficient offline inference; `think_end_token` must be a string |
| `local-completions`, `openai-completions` | OpenAI completions-compatible API | `api` | Can support `generate_until`, `loglikelihood`, `loglikelihood_rolling` if endpoint exposes logprobs and tokenizer setup works |
| `local-chat-completions`, `openai-chat-completions` | OpenAI chat-completions-compatible API | `api` | `generate_until` only; no loglikelihood/logprobs |
| `anthropic-chat`, `anthropic-chat-completions` | Anthropic chat API | `api` plus provider package availability | `generate_until` only; requires `ANTHROPIC_API_KEY` |
| `litellm`, `litellm-chat`, `litellm-chat-completions` | LiteLLM gateway | `litellm` | `generate_until` only; provider-specific credentials |
| `gguf`, `ggml` | llama.cpp/GGUF wrapper | backend package availability | Generation and loglikelihood; perplexity is not fully implemented in README table |
| `openvino` | Hugging Face Optimum/OpenVINO | `optimum` | Local converted decoder-only models |
| `ipex` | Optimum Intel IPEX | `ipex` | Intel optimized local causal models |
| `habana` | Optimum Habana | `habana` | Intel Gaudi local causal models |
| `trtllm` | TensorRT-LLM | external TensorRT-LLM stack | Hardware-specific local backend |
| `winml` | Windows ML | Windows AI packages | ONNX GenAI models on Windows CPU/GPU/NPU |
| `dummy` | Dummy LM | base | Safe smoke backend, not for real scoring |

Additional registered aliases may include multimodal/prototype and framework-specific backends such as `hf-multimodal`, `vllm-vlm`, `hf-audiolm-qwen`, `hf-mistral3`, `mamba_ssm`, `nemo_lm`, `megatron_lm`, `neuronx`, `textsynth`, `watsonx_llm`, and `steered`. Treat each as requiring its own dependency and hardware validation unless proven otherwise.

## Choosing the Backend

1. Identify the task request type:
   - Multiple-choice and many classification tasks need `loglikelihood`.
   - Perplexity tasks need `loglikelihood_rolling`.
   - Pure instruction/generation tasks can use `generate_until` only.
2. Match the endpoint:
   - Need loglikelihood through a local OpenAI-compatible server? Prefer `local-completions`, not `local-chat-completions`.
   - Need a chat-only closed model? Use a chat backend but restrict to generative tasks and verify answer extraction with a small limit.
3. Match hardware:
   - Use `hf` for reference behavior, small local models, Transformers features, PEFT/delta/GGUF via Transformers.
   - Use `vllm` or `sglang` for high-throughput local generation/loglikelihood when the model and GPU stack are supported.
   - Use `openvino`, `ipex`, `habana`, `trtllm`, or `winml` only when the machine and converted model format match.
4. Install the narrow extra and re-check imports before running a full evaluation.

## Concrete `model_args` Examples

Hugging Face local or Hub model:

```bash
lm-eval run --model hf \
  --model_args pretrained=EleutherAI/pythia-160m,dtype=float16 \
  --tasks lambada_openai --device cuda:0 --batch_size 8
```

Hugging Face with a revision and a CPU-safe dtype:

```bash
lm-eval run --model hf \
  --model_args pretrained=EleutherAI/pythia-160m,revision=step100000,dtype=float32 \
  --tasks hellaswag --device cpu --batch_size 1
```

vLLM with tensor parallelism:

```bash
lm-eval run --model vllm \
  --model_args pretrained=EleutherAI/gpt-j-6B,tensor_parallel_size=2,dtype=auto,gpu_memory_utilization=0.8 \
  --tasks lambada_openai
```

Local OpenAI-compatible completions endpoint for a loglikelihood-capable task:

```bash
lm-eval run --model local-completions \
  --model_args model=served-model,base_url=http://127.0.0.1:8000/v1/completions,tokenizer_backend=huggingface,tokenizer=EleutherAI/pythia-160m,num_concurrent=1,max_retries=3 \
  --tasks lambada_openai
```

Local OpenAI-compatible chat endpoint for a generative task:

```bash
lm-eval run --model local-chat-completions \
  --model_args model=served-chat-model,base_url=http://127.0.0.1:8000/v1/chat/completions,num_concurrent=1,max_retries=3 \
  --tasks gsm8k --apply_chat_template
```

## Registry Checks

Use the bundled checker before debugging a heavy import manually:

```bash
python scripts/check_backend_requirements.py --backend hf --backend vllm --backend local-completions
```

Expected interpretation:

- `registered: true` means the alias exists in the lazy model registry.
- `missing_packages` reports likely optional dependency packages absent from the current environment.
- `materialized: true` means the target class imported successfully; failures often identify the missing extra or incompatible platform.
