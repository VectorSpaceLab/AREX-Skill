# Prompting and tools

The pipeline can carry ordinary assistant text, TTS input text, and structured
function calls through the same ordered response path. Tool behavior differs by
LLM backend but converges on the Realtime wire protocol.

## Voice and text prompts

The package has separate prompt templates for text-first and voice-first
behavior. Use voice-oriented instructions for spoken interactions:

- Keep responses short enough for TTS and barge-in.
- Speak a natural lead-in before a physical or UI action tool.
- Avoid long Markdown/table outputs unless the client is text-only.
- When `--enable_lang_prompt` is on, expect an additional language-control
  instruction based on detected STT language.

The output processor strips or routes internal tool syntax so only clean text
is sent to TTS, while tool call events remain visible to the client.

## Local LLM tool path

For `transformers` and `mlx-lm`, tools from `session.update` are converted into
Python-like function signatures. The model is prompted to emit calls inside
`<code>...</code>` blocks, for example:

```text
<code>
web_search(query='weather in Paris')
</code>
```

The parser extracts calls, validates argument names against the generated
signature, assigns `call_id`s, and emits `response.function_call_arguments.done`.
This path is more sensitive to prompt wording and model instruction-following
than provider-native structured tool calling.

## Remote OpenAI-compatible tool path

For `responses-api`, tools are passed to the upstream provider structurally.
The provider returns function-call items, which the pipeline maps into the same
Realtime event family. `response.create` can override `tool_choice` for a single
response.

For `chat-completions`, the backend uses the OpenAI-compatible Chat
Completions request shape and its extra provider knobs. It is also the backend
used for direct audio-input models when `--stt none` is selected.

## Client tool result flow

1. Client declares tools in `session.update`.
2. Assistant emits `response.function_call_arguments.done` with `call_id`, name,
   and JSON arguments.
3. Client runs the tool.
4. Client sends `conversation.item.create` with:

```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_...",
    "output": "tool result"
  }
}
```

5. Client sends `response.create` only if the tool result needs a spoken/text
   follow-up.

For fire-and-forget actions such as robot gestures or UI state changes, the
assistant should speak the useful lead-in before the call and the client can
stop after the `conversation.item.created` acknowledgement.

## Ordering guarantees to rely on

- Assistant text parts and tool parts preserve model order.
- The output processor puts text events and TTS inputs onto one ordered queue,
  preventing later response terminals from overtaking earlier text/tool parts.
- Barge-in uses response keys and cancel generations to discard stale output
  rather than letting late TTS/LLM chunks leak into a later turn.

## Prompt debugging checklist

- If local tools are not called, inspect whether the model can follow the
  `<code>function(...)</code>` convention. A more instruction-tuned local model
  or provider-native backend may be required.
- If the assistant speaks raw tool syntax, tighten the voice prompt and confirm
  the output processor is seeing valid call syntax.
- If the assistant talks in the wrong language, use fixed STT language or enable
  the language prompt, then verify Qwen3-TTS language mapping.
- If follow-up generation loops after tool output, ensure the client sends one
  `response.create` per completed tool result batch and waits for `response.done`.
