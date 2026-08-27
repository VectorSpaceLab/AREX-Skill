# Generator and Prompt API

## Factory Selection

Use `flashrag.utils.get_generator(config)` for normal component construction. The factory selects the implementation from `framework`, the model config at `generator_model_path`, and whether the model config appears multimodal.

| Config condition | Class selected | Notes |
| --- | --- | --- |
| `framework: openai` | `OpenaiGenerator` | Uses the OpenAI-compatible async client; `openai_setting` supplies API options. |
| HF model config contains vision keys | `HFMultiModalGenerator` | Current multimodal support is HF-oriented and expects message-style multimodal inputs. |
| `framework: vllm` | `VLLMGenerator` | Uses `vllm.LLM` and `SamplingParams`; supports LoRA when `generator_lora_path` is set. |
| `framework: fschat` | `FastChatGenerator` | Extends the HF causal generator with FastChat conversation templates. |
| `framework: hf` plus T5/BART-like architecture | `EncoderDecoderGenerator` | Supports encoder-decoder models and FiD when `use_fid` is true for T5. |
| `framework: hf` otherwise | `HFCausalLMGenerator` | Uses `AutoModelForCausalLM` and tokenizer chat templates when prompts are built that way. |

Minimum generator keys usually include `framework`, `generator_model`, `generator_model_path`, `generator_max_input_len`, `generator_batch_size`, `gpu_num`, `device`, `generation_params`, and `seed` for vLLM. `Config` can fill defaults and map `generator_model` through `model2path`.

## Text Generation Calls

```python
from flashrag.config import Config
from flashrag.utils import get_generator

config = Config("my_config.yaml", config_dict={
    "framework": "hf",
    "generator_model": "my-chat-model",
    "generator_model_path": "my-org/my-chat-model",
    "generator_max_input_len": 2048,
    "generator_batch_size": 2,
    "generation_params": {"max_new_tokens": 64, "do_sample": False},
})

generator = get_generator(config)
responses = generator.generate(["Question: who is Taylor Swift?"], max_new_tokens=32)
```

Generation parameters in the method call override `generation_params` from config. FlashRAG normalizes `max_tokens` and `max_new_tokens`, but the final key differs by backend: HF/FastChat prefer `max_new_tokens`, while vLLM/OpenAI use `max_tokens` semantics. If both keys are supplied with different values, FlashRAG warns and chooses one according to the backend helper path.

## Return Shapes

| Backend | Default return | Optional returns |
| --- | --- | --- |
| HF causal | `List[str]` | `return_scores=True` returns `(responses, scores)`; `return_dict=True` returns responses plus generated token ids/logits/scores. |
| Encoder-decoder | `List[str]` | Stop-word criteria are supported through `stop` in generation parameters. |
| vLLM | `List[str]`, or nested text when multiple candidates are returned | `return_raw_output=True` returns vLLM outputs; `return_scores=True` returns scores when logprobs are available. |
| OpenAI | `List[str]` | `return_scores=True` requests logprobs where supported; OpenAI chat and completion modes are both supported. |
| Multimodal HF | `List[str]` | Generation params pass through to the model-specific inference engine. |

## PromptTemplate

`flashrag.prompt.PromptTemplate` builds prompts from a config, optional system/user templates, a reference template, and chat enablement.

```python
from flashrag.prompt import PromptTemplate

template = PromptTemplate(config)
prompt = template.get_string(
    question="Who directed Polish-Russian War?",
    retrieval_result=[{"contents": "Polish-Russian War\nA film directed by Xawery Żuławski."}],
)
```

Important behavior:

- Default placeholders are `question` and `reference`; custom templates should include the fields they format.
- For `framework: openai`, prompts are chat message lists when chat is enabled.
- For non-OpenAI chat or instruct models, FlashRAG tries `tokenizer.apply_chat_template(..., add_generation_prompt=True)`.
- If chat templates are unavailable, FlashRAG falls back to joining system and user text.
- `get_string(messages=...)` accepts either a string or message dictionaries and truncates to `generator_max_input_len`.
- `previous_gen` appends prior assistant text for iterative generation methods.

## Reference Formatting

`PromptTemplate.format_reference(retrieval_result)` expects each retrieved document to contain a `contents` field where the first line is treated as the title and the remaining lines as body text. The default format is `Doc N(Title: title) body`. If your retrieval output uses another schema, convert it before calling the template.

## Common Usage Pattern

1. Build or load a `Config` with generator keys.
2. Construct a `PromptTemplate` with matching chat settings.
3. Convert dataset items and retrieved documents into prompt strings or OpenAI message lists.
4. Call `generator.generate(input_list, **override_params)`.
5. Keep backend-specific return options explicit when scores, raw outputs, or logits are needed.
