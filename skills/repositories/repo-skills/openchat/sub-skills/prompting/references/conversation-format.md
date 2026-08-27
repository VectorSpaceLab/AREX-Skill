# Conversation format and tokenization

OpenChat prompting is built around three Pydantic models from `ochat.config`: `Message`, `Conversation`, and `ConversationTemplate`. This reference focuses on formatting and tokenization behavior; use [model-overview](model-overview.md) for model registry choices.

## Core objects

```python
from ochat.config import Conversation, ConversationTemplate, Message, MODEL_CONFIG_MAP

config = MODEL_CONFIG_MAP["openchat_3.6"]
tokenizer = config.model_tokenizer_create("MODEL_WEIGHTS_OR_LOCAL_MODEL")
template = config.conversation_template(tokenizer=tokenizer)

conv = Conversation(
    system="You are concise.",
    condition="GPT4 Correct",
    items=[
        Message(role="user", content="Explain EOT.", weight=0.0),
        Message(role="assistant", content="EOT marks the end of a turn.", weight=1.0),
    ],
)
tokens, weights = template.tokenize_conversations([conv], inference=False)
```

`Message.weight` is optional at the schema level because inference does not need it. Training/non-inference tokenization asserts that every message has a weight.

## Field semantics

| Field | Meaning | Prompting notes |
| --- | --- | --- |
| `Message.role` | Usually `user` or `assistant`; `system` is handled separately by serving | The template does not validate roles by itself, but some role-prefix functions do. `gemma_it` maps only `user` and `assistant`. |
| `Message.content` | Raw message text | User content is tokenized separately from role prefixes; special-token handling depends on the tokenizer path described below. |
| `Message.weight` | Loss weight for this message | Required when `inference=False`; ignored when `inference=True`. Prefix/BOS/system tokens always receive zero weight. |
| `Conversation.items` | Ordered user/assistant turns | Serving appends an empty assistant turn when the last request message is not already `assistant`. |
| `Conversation.condition` | C-RLFT or inference condition string | Empty inference uses the model template's default; non-inference defaults to empty. |
| `Conversation.system` | System prompt text | System text is emitted before normal messages when non-empty. Serving ignores system messages unless system prompts are enabled. |

## Tokenization algorithm

`ConversationTemplate.tokenize_conversations(conversations, inference=False, seq_level_weight=False)` performs these steps:

1. Cache a default condition: template `inference_condition` when `inference=True`, otherwise empty.
2. Pre-tokenize unique system strings, role prefixes, and message texts.
3. Start each conversation with tokenizer BOS tokens from `tokenizer("").input_ids`; those tokens get zero weight.
4. If `Conversation.system` is non-empty:
   - add the `system` role prefix only when the template was created with `system_as_role=True`;
   - add the system text;
   - add EOT;
   - assign zero weight to all system-related tokens.
5. For each message:
   - add `role_prefix(message.role, conv.condition or default_condition)` with zero weight;
   - add message content tokens;
   - when `inference=False`, copy `Message.weight` to content tokens and EOT tokens;
   - add EOT after the message unless this is the final message in inference mode.
6. Return `(result_tokens, result_weights)`.

The last-turn inference EOT rule is intentional: the empty assistant generation prefix should not already contain a stop marker.

## Inference format

For direct Python inference tokenization, build a conversation with an empty assistant final turn:

```python
conv = Conversation(
    condition="",  # uses the template's default inference condition
    system="",
    items=[
        Message(role="user", content="Who won the 2018 World Cup?"),
        Message(role="assistant", content="France."),
        Message(role="user", content="Who won in 2022?"),
        Message(role="assistant", content=""),
    ],
)
tokens, _ = template.tokenize_conversations([conv], inference=True)
```

OpenChat serving follows the same pattern in `AsyncTokenizer.tokenize`: it reads OpenAI-style messages, optionally extracts a system prompt, appends `Message(role="assistant", content="")` if needed, and tokenizes with `inference=True`.

### Default condition in inference

If `conv.condition` is empty:

- `openchat_3.6` uses `GPT4 Correct`.
- `openchat_v3.2_mistral` and `openchat_v3.2_gemma_new` use `GPT4 Correct`.
- `openchat_v3.2` uses `GPT4`.
- compatibility templates with empty `inference_condition` emit no condition.

To use math mode, set the condition explicitly:

```python
conv = Conversation(
    condition="Math Correct",
    items=[Message(role="user", content="10.3 - 7988.8133 = "), Message(role="assistant", content="")],
)
```

`Math Correct` is a condition string, not a separate model type.

## Training/non-inference format

For training/data tokenization, each message must include a weight:

```python
conv = Conversation(
    condition="GPT4",
    system="",
    items=[
        Message(role="user", content="What is C-RLFT?", weight=0.0),
        Message(role="assistant", content="A mixed-quality data training method.", weight=1.0),
    ],
)
tokens, weights = template.tokenize_conversations([conv], inference=False)
```

Use the loss weights to control supervision. Common SFT convention is `0.0` for user messages and `1.0` for assistant responses. C-RLFT convention uses class weights on assistant responses, such as lower weights for weaker classes and higher weights for stronger classes. OpenChat's README examples show `GPT3`/`GPT4` classes with different assistant weights.

When `seq_level_weight=True`, each non-prefix message weight is divided by `len(message_tokens) + len(eot_tokens)`. This makes a message's total contribution closer to the original sequence-level weight instead of applying the same scalar to every token.

## EOT and weights

EOT tokens are treated as part of the message for loss weighting in training/non-inference mode:

- role prefix weights: always `0.0`;
- message content weights: `Message.weight`;
- EOT after a message: `Message.weight`;
- BOS and system tokens: `0.0`.

In inference mode, `result_weights` contains `None` for message content/EOT positions and `0.0` for prefix/system/BOS positions, but callers normally ignore weights.

## System prompt handling

There are two layers of system-prompt behavior:

1. `ConversationTemplate` behavior: when `Conversation.system` is non-empty, the system text is added before normal messages. If `system_as_role=True`, a system role prefix is emitted; otherwise system text is emitted without a role prefix, followed by EOT.
2. Serving behavior: OpenAI-style request messages with role `system` are used only when the server was started with system prompts enabled. Otherwise they are skipped before tokenization.

Practical rule: if a tokenized prompt must include a system prompt, set `Conversation.system` directly in direct Python code, or enable the server's system-prompt option in serving workflows.

## HF chat template notes

Some OpenChat configs include an `hf_chat_template`. Repo tests compare `tokenize_conversations(..., inference=True)` against `tokenizer.apply_chat_template(..., add_generation_prompt=True)` for configs that define one. Use the bundled template when you need Hugging Face chat-template compatibility, but remember that OpenChat's direct tokenization still uses `ConversationTemplate` as the source of truth.

## Tokenizer special-token path

`ConversationTemplate._tokenize` handles fast and slow tokenizers differently:

- Fast tokenizers temporarily set `tokenizer._tokenizer.encode_special_tokens` while tokenizing.
- Slow tokenizers pass `split_special_tokens=...`.

Role prefixes and EOT are tokenized with special-token handling disabled where appropriate; message text and system text are tokenized through the content path. If a user literally types strings that look like special tokens, verify whether the selected tokenizer treats them as control tokens or plain text.
