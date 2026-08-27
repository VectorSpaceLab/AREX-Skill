# Template Reference

Templates control how ms-swift converts `messages`, tools, media placeholders, and loss masks into model inputs. Model registration connects `model_type` to a default template; CLI `--template` overrides it when automatic detection is wrong or intentionally changed.

## Model and Template Selection

ms-swift can infer `model_type` from a model ID/path suffix and `config.json` architectures. Each `ModelMeta` can define:

- `model_type`: unique CLI/model registry identifier.
- `template`: default template when `--template` is not provided.
- `model_groups`: model IDs and optional per-group template overrides.
- `architectures`: config values used for automatic matching.
- `is_multimodal`, `is_reward`, `task_type`, and `model_arch`: behavior flags used by loading and training.

Selection order for templates is effectively:

1. Explicit `--template` or `get_template(..., template_type=...)`.
2. Template recorded in model arguments for a saved checkpoint, when present.
3. Template from matched `ModelMeta` or `ModelGroup`.
4. Error if multiple/no candidates remain.

Use explicit `--model_type` and `--template` together when registering a new model or when a local repo/model directory does not match the intended built-in mapping.

## Inspect Before Overriding

Use registry inspection to find the expected pair:

```bash
python scripts/inspect_registries.py --models --templates --contains Qwen2.5
python scripts/inspect_registries.py --models --contains qwen2 --limit 30
```

Look for these fields:

- Model `model_type`.
- Default `template`.
- Candidate templates on model groups.
- Requirements that may need package upgrades.
- Whether the model is multimodal or reward-style.
- Template `agent_template`, system support, and multi-round support.

Do not assume that base and chat models use interchangeable templates. A base model may need a generation template or `use_chat_template=False`, while an instruct/chat model usually needs the chat template expected by its tokenizer.

## `get_processor` and `get_template`

The public Python path is:

```python
from swift import get_processor, get_template

processor = get_processor(
    "Qwen/Qwen2.5-7B-Instruct",
    model_type="qwen2",          # optional override
    download_model=False,         # avoid downloading weights when possible
)
template = get_template(
    processor,
    template_type="qwen2_5",     # optional override
    loss_scale="default",
    agent_template=None,
)
```

`get_processor` loads tokenizer/processor metadata, not model weights. It may still need local tokenizer files or hub access. For offline checks, use local model directories or cached models and pass `download_model=False`.

`get_template` accepts important options:

| Option | Use |
| --- | --- |
| `template_type` | Force a template instead of auto-detection. |
| `default_system` | Override the template default system prompt. |
| `max_length` and `truncation_strategy` | Control max-length handling. |
| `max_pixels` | Bound multimodal image pixels for compatible models. |
| `agent_template` | Select tool/agent formatting such as ReAct/Hermes-style templates. |
| `norm_bbox` | Choose bbox normalization for grounding where supported. |
| `use_chat_template` | Disable chat formatting for generation-style use cases. |
| `loss_scale`, `is_binary_loss_scale` | Training label/loss-mask behavior. |
| `template_backend` | `swift` or `jinja` rendering where supported. |
| `enable_thinking`, `preserve_thinking`, `response_prefix` | Thinking and response-prefix controls. |

## Encoding Modes

Set mode before checking training/RLHF behavior:

```python
template.set_mode("train")
encoded = template.encode({"messages": [...]})
print(template.safe_decode(encoded["input_ids"]))
print(template.safe_decode(encoded["labels"]))
```

For preference data, use the relevant RLHF mode so chosen/rejected labels are generated:

```python
template.set_mode("rlhf")
encoded = template.encode(row)
print(template.safe_decode(encoded["chosen_labels"]))
print(template.safe_decode(encoded["rejected_labels"]))
```

The bundled `scripts/inspect_template_encoding.py` defaults to a no-network plan. Add `--attempt --no-download` only when the tokenizer/processor is already available locally or cached.

## Agent Templates

Agent formatting uses both row fields and template configuration:

- `tools` describes available functions and is merged into the system section by the selected agent template.
- `tool_call` messages are converted into model-specific assistant/tool-call text.
- `tool_response` and `tool` messages are converted into observation/tool-response text and generally do not train as assistant loss.
- Some templates support parallel tool calls; others serialize or restrict them.

If tool rows encode incorrectly, inspect both `--template` and `--agent_template`. A model's default template may have a default agent template, but explicit overrides are safer during migration.

## Loss and Loss Scale

ms-swift supports both command-level `--loss_scale` strategies and message-level overrides:

- `loss: false` on an assistant message suppresses loss for that assistant span.
- `loss: true` forces loss for that assistant span under the selected strategy.
- `loss_scale: 0.0`, `1.0`, `2.0`, etc. weights assistant spans.
- Values greater than `1` require non-binary loss-scale handling in the training configuration.
- On consecutive `tool_call` messages, only the first call's loss/loss-scale settings may take effect.

Use template encoding checks for any non-default loss strategy, especially with thinking tags such as `<think>...</think>` and agent/tool spans.

## Multimodal and Grounding Templates

Multimodal templates determine how `<image>`, `<video>`, `<audio>`, `<ref-object>`, and `<bbox>` placeholders become model inputs. Check:

- Whether the model's template supports the requested media types.
- Whether `images`, `videos`, and `audios` counts match placeholders.
- Whether `chat_template_kwargs` keys are accepted by the target model family.
- Whether grounding boxes use real coordinates, normalized coordinates, or model-specific formatting.
- Whether local files, URLs, or base64 data are valid in the execution environment.

For Qwen-VL-style models, pixel bounds and bbox formatting can be model-family-specific. Keep those decisions with the template/model pair, not just the dataset row.

## Base-to-Chat Mismatch

Symptoms of a mismatch include duplicated role markers, missing assistant prompts, model outputs that continue the user message, no EOS behavior, or label masks over the wrong span.

Common corrections:

- Use the chat/instruct template for chat-tuned models.
- Use a generation template or disable chat formatting for base completion models.
- Explicitly set `--template` when a local model directory has ambiguous metadata.
- Confirm that tokenizer special tokens match the registered template strings.
- Keep `--model_type` and `--template` overrides paired when using a custom plugin.

## Offline/Local Model Loading

For local-only checks:

```bash
python scripts/inspect_template_encoding.py \
  --model ./local-model-dir \
  --model-type my_model_type \
  --template my_chat_template \
  --attempt --no-download
```

If this fails, separate causes:

- Registry problem: `model_type` or `template` is absent from mappings.
- Local files problem: tokenizer/processor config is missing.
- Optional dependency problem: the model loader requires an extra package.
- Template problem: `get_template` cannot choose a candidate or rejects the system prompt.

Registry inspection can still pass when local tokenizer files are missing, because mapping inspection does not load model assets.
