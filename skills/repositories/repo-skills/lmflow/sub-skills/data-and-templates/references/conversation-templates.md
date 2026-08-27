# Conversation Templates

## Built-In Templates

`lmflow.utils.conversation_template.PRESET_TEMPLATES` exposes built-in templates such as:

- `chatglm3`
- `chatml`
- `deepseek`, `deepseek_v2`, `deepseek_v3`, `deepseek_r1`, `deepseek_r1_distill`
- `empty`, `empty_no_special_tokens`, `disable`
- `gemma`
- `hymba`
- `internlm2`
- `llama2`, `llama3`, `llama3_for_tool`
- `phi3`
- `qwen2`, `qwen2_for_tool`, `qwen2_5`, `qwen2_5_1m`, `qwen2_5_math`, `qwen_qwq`, `qwen3`
- `yi`, `yi1_5`
- `zephyr`

When the installed Transformers version is new enough, LMFlow also exposes newer Jinja-based templates for DeepSeek, Qwen, and Gemma variants.

## Template Selection

Choose the template that matches the model family or the training data format:

- `llama2` and `llama3` for Llama-style chat models;
- `chatml` for ChatML-style models;
- `qwen2` and `qwen2_5` for Qwen-family chat models;
- `deepseek_*` for DeepSeek chat families;
- `empty` or `empty_no_special_tokens` when the dataset already contains formatted turn markers.

## Customization Pattern

LMFlow templates are built from formatters that combine string and token components. The customization steps are:

1. decompose the conversation into system, user, assistant, and optional tool messages;
2. choose the string/token formatter for each role;
3. register the new template in the package template registry;
4. use the template name from the training or inference command.

## Common Pitfalls

- Do not invent a template name; print the installed preset list first.
- Do not assume the tokenizer template and the LMFlow preset are identical.
- Do not use a template that the installed Transformers version does not support.
- Do not forget that `empty` adds special tokens while `empty_no_special_tokens` does not.
