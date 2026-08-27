# System Prompts

## When to read

Read this when the user wants to control Qwen-Chat behavior with a system instruction: role play, language style, task specialization, or behavioral constraints.

## Core pattern

Qwen chat checkpoints accept a `system` argument through `model.chat`:

```python
response, history = model.chat(
    tokenizer,
    "你好呀",
    history=None,
    system="请用二次元可爱语气和我说话",
)
```

For English prompts:

```python
response, history = model.chat(
    tokenizer,
    "My colleague works diligently",
    history=None,
    system="You will write beautiful compliments according to needs",
)
```

Use chat checkpoints, not base checkpoints, when the user expects stable behavior over multi-turn dialogue.

## Good system prompt uses

- Role play: define the persona and boundaries of the persona.
- Language style: ask for tone, language, brevity, or formatting behavior.
- Task setting: make the assistant focus on a task family.
- Behavior setting: specify refusal, safety, or process rules.

## Practical cautions

- A system prompt is not a security boundary. Use application-level validation for unsafe outputs.
- If the behavior is not stable across turns, confirm the user loaded a chat checkpoint and preserves `history` correctly.
- Do not mix system-prompt debugging with server deployment; first verify the same prompt through a local `model.chat` path or a controlled API request.
