# Model and Backend Options

## Core Generator Config

FlashRAG generator setup is controlled primarily by these keys:

```yaml
framework: vllm
model2path:
  llama3-8B-instruct: meta-llama/Meta-Llama-3-8B-Instruct
generator_model: llama3-8B-instruct
generator_model_path: null
generator_max_input_len: 2048
generator_batch_size: 4
generation_params:
  max_tokens: 32
  do_sample: false
```

`Config` resolves `generator_model_path` from `model2path` when possible. If the mapping is absent, set `generator_model_path` directly to a model identifier or a valid local model directory. Do not assume `generator_model` alone is enough for local/offline runs.

## Backend Matrix

| Framework | Best use | Main dependencies | Parameter notes |
| --- | --- | --- | --- |
| `hf` | Debuggable local Transformers inference, encoder-decoder models, logits/token details | `torch`, `transformers`, `tqdm`; optional PEFT support for adapters | Uses `max_new_tokens`; supports `return_dict` for token ids/logits in causal LM. |
| `vllm` | High-throughput local LLM inference | `vllm`, `torch`, `transformers` | Uses vLLM `SamplingParams`; `do_sample: false` is converted to `temperature: 0`; adds Llama-3 stop handling. |
| `fschat` | FastChat template-driven serving/inference path | FastChat plus HF stack | Uses FastChat conversation templates and inherits HF causal generation behavior. |
| `openai` | API-backed generation through OpenAI-compatible clients | `openai`, `tiktoken`, network/API credentials | Uses `max_tokens`; strips `do_sample`; supports chat and completion modes. |

## OpenAI-Compatible Backend

Minimal shape:

```yaml
framework: openai
generator_model: gpt-4o-mini
generator_batch_size: 4
generator_max_input_len: 8192
generation_params:
  max_tokens: 128
  temperature: 0
openai_setting:
  api_key: null
  base_url: null
```

If `openai_setting.api_key` is `null`, FlashRAG reads `OPENAI_API_KEY` from the environment. For Azure-compatible usage, include `api_type: azure` plus the settings expected by the OpenAI Python client, such as endpoint and API version. Keep real credentials outside YAML examples and reports.

`OpenaiGenerator.generate(...)` chooses chat mode when the input is a list of message dictionaries or a list containing message lists. It chooses completion mode when the input is plain strings.

## vLLM Backend

`VLLMGenerator` loads `vllm.LLM(generator_model_path, tensor_parallel_size=..., gpu_memory_utilization=..., max_model_len=...)`. Useful optional keys:

- `gpu_memory_utilization`: defaults to `0.85` if omitted.
- `gpu_num`: used for tensor parallel size; odd values above 1 are reduced by one.
- `generator_lora_path`: enables vLLM LoRA request handling.
- `seed`: copied into sampling params.

For vLLM, avoid passing HF-only generation fields unless vLLM `SamplingParams` supports them. If both `max_tokens` and `max_new_tokens` appear, FlashRAG resolves to `max_tokens` semantics for this path.

## HF and FastChat Backends

HF causal generation loads `AutoModelForCausalLM` with `torch_dtype="auto"`, `device_map="auto"`, and `trust_remote_code=True`; tokenizer padding is left-sided and non-Qwen tokenizers use EOS as pad token. Encoder-decoder generation loads T5/BART-style classes based on model architecture and can use FiD for T5 when `use_fid` is true.

FastChat extends the HF causal generator and uses FastChat conversation templates. It is useful when the model’s expected chat format is covered by FastChat better than by tokenizer `apply_chat_template`.

## Multimodal Generation

FlashRAG detects multimodal models by reading `config.json` under `generator_model_path` and checking for vision-related keys. Multimodal generation currently uses HF-oriented classes, with supported families including Qwen2-VL, InternVL2, LLaVA, and LLaVA-next style engines.

Input format is a list of message lists:

```python
messages = [[
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "sample.png"},
            {"type": "text", "text": "Describe this image in one sentence."},
        ],
    }
]]
output = generator.generate(messages, batch_size=1, max_new_tokens=128)
```

Images may be local paths, URLs, or PIL images depending on the model path. Qwen2-VL requires `qwen_vl_utils`; several multimodal branches also need PIL/image processing packages and model-specific `trust_remote_code` support.

## Prompt and Tokenizer Alignment

- Build chat prompts with `PromptTemplate` when using text-only chat/instruct models.
- Do not feed raw untemplated text into a chat model unless the model was trained for that format.
- Confirm `generator_max_input_len` is below the model/backend maximum; `PromptTemplate` truncates, but truncation may remove useful context.
- For OpenAI, `tiktoken` may fall back to `gpt-3.5-turbo` encoding when the model name is unknown.
- For multimodal generators, do not use `PromptTemplate`; construct message blocks with image/text content directly.
