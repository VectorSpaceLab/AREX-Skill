# Model overview for OpenChat prompting

This reference is for choosing the correct OpenChat model configuration before formatting prompts. It is not a serving or benchmark guide; route those tasks to [serving](../../serving/SKILL.md) or [evaluation](../../evaluation/SKILL.md).

## Name taxonomy

OpenChat code uses three different names that are easy to confuse:

- **Weight repository/path**: the model weights and tokenizer loaded by Transformers or vLLM, such as `openchat/openchat-3.6-8b-20240522`.
- **Canonical model type**: the key in `MODEL_CONFIG_MAP`; use this for direct Python configuration, evaluation `--model-type`, training/data tokenization options, and serving `--model-type` when supplied manually.
- **Serving alias**: a user-facing name accepted by the OpenAI-compatible server after it has already loaded a canonical model type. Serving aliases are not always valid `MODEL_CONFIG_MAP` keys.

If the server auto-detects model type, it reads `openchat.json` from the model cache/repository. In offline or custom-cache situations, pass the canonical `--model-type` explicitly rather than passing a serving alias.

## Registry facts

| Canonical model type | Serving aliases | Context | Tokenizer factory | Prompt family | Default inference condition | EOT string | HF chat template |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `openchat_3.6` | none | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=True)` | Llama-3/OpenChat headers | `GPT4 Correct` | `<|eot_id|>` | yes |
| `openchat_v3.2` | none | 4096 | `AutoTokenizer.from_pretrained(..., use_fast=False)` | OpenChat v3.2 text roles | `GPT4` | `<|end_of_turn|>` | no |
| `openchat_v3.2_mistral` | `openchat_3.5` | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=True)` | OpenChat v3.2 text roles | `GPT4 Correct` | `<|end_of_turn|>` | yes |
| `openchat_v3.2_gemma_new` | `openchat_3.5_gemma_new` | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=True)` | OpenChat v3.2 text roles | `GPT4 Correct` | `<end_of_turn>` | yes |
| `chatml_8192` | none | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=True)` | ChatML | empty | `<|im_end|>` | no |
| `zephyr_mistral` | none | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=False)` | Zephyr roles | empty | `</s>` | no |
| `gemma_it` | none | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=False)` | Gemma IT roles | empty | `<end_of_turn>` | no |
| `llama3_instruct` | none | 8192 | `AutoTokenizer.from_pretrained(..., use_fast=True)` | Llama-3 Instruct headers | empty | `<|eot_id|>` | no |

Context length is enforced by serving as the sum of prompt tokens plus requested generation tokens. Evaluation tokenization also clips prompt tokens to the last `model_max_context` tokens.

## Prompt families

### OpenChat 3.6 / Llama 3 headers

`openchat_3.6` uses header special tokens around role names. The condition is part of the user/assistant header when present:

```text
<|start_header_id|>GPT4 Correct User<|end_header_id|>

Hello<|eot_id|><|start_header_id|>GPT4 Correct Assistant<|end_header_id|>

```

System text is represented as a real system role header:

```text
<|start_header_id|>System<|end_header_id|>

You are concise.<|eot_id|>
```

### OpenChat v3.2 text-role family

`openchat_v3.2`, `openchat_v3.2_mistral`, and `openchat_v3.2_gemma_new` use text prefixes of the form:

```text
GPT4 Correct User: Hello<|end_of_turn|>GPT4 Correct Assistant:
```

The Gemma-new variant uses `<end_of_turn>` instead of `<|end_of_turn|>`.

### Compatibility templates

`chatml_8192`, `zephyr_mistral`, `gemma_it`, and `llama3_instruct` exist in the registry for compatible formatting, but their role-prefix functions ignore the OpenChat condition string. Use them only when the loaded tokenizer/model actually matches that format.

## Condition behavior

`Conversation.condition` is an arbitrary string. It is inserted only by templates whose `role_prefix` uses the condition argument.

- In **inference**, an empty `Conversation.condition` falls back to the template's `inference_condition`.
- In **training/non-inference tokenization**, the default condition is empty; set `Conversation.condition` yourself for C-RLFT labels such as `GPT3`, `GPT4`, or another class label.
- `GPT4 Correct` is the default inference condition for `openchat_3.6`, `openchat_v3.2_mistral`, and `openchat_v3.2_gemma_new`.
- `Math Correct` is not a separate model type. It is a condition override used for math-oriented prompting on OpenChat models that consume conditions.
- A custom condition is included verbatim in the role prefix. Check spacing and capitalization; token mismatches often come from `GPT4 Correct` vs `GPT4`, or from passing an alias as a model type.

## Model type versus serving alias

Use canonical model types in code that indexes `MODEL_CONFIG_MAP`:

```python
from ochat.config import MODEL_CONFIG_MAP
config = MODEL_CONFIG_MAP["openchat_v3.2_mistral"]
```

Use serving aliases only after a server has advertised them via its model list. For example, a server loaded with canonical type `openchat_v3.2_mistral` accepts both `openchat_v3.2_mistral` and `openchat_3.5` as request `model` values, but `openchat_3.5` is not the canonical key to use for direct tokenization.

## Special-token compatibility

The tokenizer and model weights must include the template's EOT and header tokens. OpenChat's own training guidance calls out these requirements:

- Llama 3/OpenChat 3.6: `<|eot_id|>`, `<|start_header_id|>`, and `<|end_header_id|>` must exist and have initialized embeddings.
- Mistral/OpenChat 3.5-style models: `<|end_of_turn|>` must exist and have initialized embeddings.

If the tokenizer maps the EOT string to multiple IDs, serving's tokenizer helper asserts because it expects one stop token ID. Recreate the tokenizer/template after changing special tokens; `ConversationTemplate` caches BOS and EOT IDs at construction time.
