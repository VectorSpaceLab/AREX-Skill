# Chat Templates

Chat templates control how strings or OpenAI-style message lists become the actual prompt sent to the model. Use this reference when output quality suggests the prompt format is wrong, when a model needs a non-default format, or when a LoRA adapter expects its own template.

## When to Override

Consider overriding the chat template when:

- The model echoes role markers or emits raw `<|im_start|>` / `<|im_end|>` style tokens unexpectedly.
- A chat model behaves like a completion model or ignores system instructions.
- The prompt format changed between base model, instruct model, and LoRA adapter.
- The user provides a model family whose template is not registered in the installed LMDeploy version.
- Offline pipeline behavior differs from a known Hugging Face `apply_chat_template` rendering.

Do not solve VLM image/video placeholder rules here; route multimodal content details to `vision-language`.

## Built-In and HF Templates

LMDeploy registers chat template classes in `lmdeploy.model.MODELS`. Many model families use built-ins, and the `hf` template can delegate to the tokenizer’s Hugging Face chat template.

Safe no-model inspection:

```bash
python sub-skills/pipeline-inference/scripts/inspect_pipeline_config.py --json
```

The JSON output includes available registered template names from the installed package.

Programmatic use:

```python
from lmdeploy import ChatTemplateConfig, pipeline

chat_template_config = ChatTemplateConfig(model_name="hf", model_path="org/model-or-local-path")
with pipeline("org/model-or-local-path", chat_template_config=chat_template_config) as pipe:
    print(pipe([[{"role": "user", "content": "Hello"}]]).text)
```

If `model_name` is unknown, `ChatTemplateConfig.chat_template()` warns and falls back to `BaseChatTemplate`; that may not be correct for instruct models.

## JSON Chat Template

A JSON file can define the template directly:

```json
{
  "model_name": "customized_model",
  "system": "<|im_start|>system\n",
  "meta_instruction": "You are a helpful assistant.",
  "eosys": "<|im_end|>\n",
  "user": "<|im_start|>user\n",
  "eoh": "<|im_end|>\n",
  "assistant": "<|im_start|>assistant\n",
  "eoa": "<|im_end|>",
  "separator": "\n",
  "capability": "chat",
  "stop_words": ["<|im_end|>"]
}
```

Python pipeline usage:

```python
from lmdeploy import ChatTemplateConfig, pipeline

chat_template_config = ChatTemplateConfig.from_json("chat_template.json")
with pipeline("org/model-or-local-path", chat_template_config=chat_template_config) as pipe:
    print(pipe([[{"role": "user", "content": "Who are you?"}]]).text)
```

CLI usage:

```bash
lmdeploy chat org/model-or-local-path --chat-template chat_template.json
```

`ChatTemplateConfig.from_json(...)` accepts a file path or JSON string. If `model_name` is missing, LMDeploy creates a random name and registers `BaseChatTemplate` for it.

## Python Template Registration

Use a Python class when formatting requires more control than JSON fields:

```python
from lmdeploy import ChatTemplateConfig, pipeline
from lmdeploy.model import MODELS, BaseChatTemplate


@MODELS.register_module(name="customized_model")
class CustomizedModel(BaseChatTemplate):
    def __init__(self, **kwargs):
        super().__init__(
            system="<|im_start|>system\n",
            meta_instruction="You are a helpful assistant.",
            eosys="<|im_end|>\n",
            user="<|im_start|>user\n",
            eoh="<|im_end|>\n",
            assistant="<|im_start|>assistant\n",
            eoa="<|im_end|>",
            separator="\n",
            stop_words=["<|im_end|>"],
            **kwargs,
        )


chat_template_config = ChatTemplateConfig("customized_model")
with pipeline("org/model-or-local-path", chat_template_config=chat_template_config) as pipe:
    print(pipe([[{"role": "user", "content": "Who are you?"}]]).text)
```

Keep registration code in the same Python process before constructing the pipeline. For reusable applications, put the registration in an imported module and import it before `pipeline(...)`.

## Prompt Rendering Model

`BaseChatTemplate` roughly renders the first user turn as:

```text
{system}{meta_instruction}{eosys}{user}{user_content}{eoh}{assistant}
```

Later turns add the separator and user/assistant wrappers. For `messages2prompt`, LMDeploy maps roles through user/assistant/system/tool delimiters, uses the first text part if `content` is a list, and appends the assistant prefix unless the last message is an assistant prefix.

Set `capability="completion"` when the model should receive raw completion text without chat wrappers.

## Stop Words and Token IDs

Chat templates often define `stop_words`. `GenerationConfig.convert_stop_bad_words_to_ids(tokenizer)` can turn `stop_words` / `bad_words` into token ids and merge them with explicit `stop_token_ids` / `bad_token_ids`.

Guidelines:

- Prefer template stop words for role/end markers such as `<|im_end|>`.
- Prefer `stop_token_ids` when the exact token id is known and tokenizer-stable.
- Validate user-provided `stop_words` and `bad_words` are lists of strings.
- Keep `include_stop_str_in_output=False` unless the caller explicitly needs the stop text.

## Debugging Template Mismatch

1. Set `log_level="INFO"` or a suitable `max_log_len` during pipeline construction to inspect prompt logging where available.
2. Compare a one-turn message prompt against the tokenizer’s `apply_chat_template(..., tokenize=False, add_generation_prompt=True)` when using an HF template.
3. Check whether the model id matches an LMDeploy built-in template in the installed registry.
4. Try `ChatTemplateConfig(model_name="hf", model_path=model_path)` for Hugging Face instruct models with a reliable tokenizer template.
5. Try `capability="completion"` only for completion models or code infilling tasks that must avoid chat wrappers.
6. Add or adjust stop words when the model keeps generating assistant/user delimiters.

## Trust and Download Boundaries

- `trust_remote_code=False` is safer and should remain the default unless the model/tokenizer requires custom remote code.
- If `trust_remote_code=True`, explain that remote Python code from the model repository may execute during model/tokenizer loading.
- A model repo id may trigger downloads; use local paths for fully offline or hermetic workflows.
- The inspection script does not load remote templates, tokenizers, or models.
