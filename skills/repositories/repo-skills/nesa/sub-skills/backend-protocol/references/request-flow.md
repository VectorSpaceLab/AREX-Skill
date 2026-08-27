# Request Flow

This reference explains the remote encrypted LLM request flow without requiring a
live Nesa endpoint call.

## Prompt construction

The helper builds a message list from:

- the current user message;
- a system prompt;
- recent history pairs; and
- a lookback limit, defaulting to 10 history pairs.

Each content string is cleaned before inclusion. History becomes alternating
user/assistant messages, then the current user message is appended after the
system instruction.

## Local tokenization

For encrypted Llama chat, the tokenizer is local. The flow applies the tokenizer
chat template to the prompt messages with generation prompt enabled. The
resulting token IDs are printed/used as the server-visible encrypted payload.

## Inference request shape

A request preview should include:

- `stream: true`
- a unique `correlation_id`
- a model id expected by the remote service
- one assistant-role message whose content is the token-id list string
- `session_id: {"ee": true}`
- `model_params`, often empty unless the user provided sampling settings

The source mapping resolves the web UI encrypted Llama key to a backend model id
like `meta-llama/Llama-3.1-8B-Instruct-ee`. If a new model is added, update the
mapping and registry together.

## Streaming response handling

The streaming client reads server-sent-event blocks, decodes JSON chunks into
`InferenceResponse`, and yields `delta.content` until a finish reason appears.
When content is an integer token, local tokenizer decoding turns it into text;
when content is a string, the UI wraps it in a file marker convention.

## Safe preview vs live call

Use `scripts/build_llm_request_preview.py` to produce a payload skeleton without
network access. A preview can validate role ordering, model mapping, session
shape, and sampling parameters. It cannot verify endpoint availability,
authentication, or encrypted model output.

Only make a live stream call after the user explicitly requests it and accepts
network/service dependencies.
