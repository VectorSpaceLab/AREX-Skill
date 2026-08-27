# Nesa Web UI Integration

This reference summarizes the Nesa-specific web UI integration without requiring
future agents to inspect the original checkout.

## Model menu and registry dispatch

The model UI displays available models and lets users load/unload models. For
Nesa model names, loading is dispatched through a registry:

- model-specific handlers are checked before task-type handlers;
- unsupported model/task keys raise a clear `ValueError`;
- the UI stores the selected model name in shared state before loading.

For supported Nesa models, the handler returns a tokenizer and model object. The
remote encrypted LLM handler intentionally returns a tokenizer plus `None` for
local model weights because the model inference happens through the remote Nesa
service.

## Download helper behavior

The model-download helper can:

- normalize model names and optional `model:branch` syntax;
- validate branch names using only letters, digits, dot, underscore, and dash;
- query Hugging Face model trees;
- choose output folders under `models/` or `loras/`;
- prefer safetensors over duplicate PyTorch/GGUF files when both exist;
- resume downloads; and
- verify SHA-256 checksums when metadata is present.

Use the bundled `check_hf_model_plan.py` helper to preview normalization and
output paths without contacting Hugging Face.

## Local DistilBERT handler

The local classifier handler loads a tokenizer and
`AutoModelForSequenceClassification` from a local model directory, then yields two
Markdown tables:

1. encrypted token IDs from the tokenizer;
2. classification label probabilities from `config.id2label`.

When a user asks about output interpretation, route to the encrypted-distilbert
sub-skill.

## Remote encrypted LLM handler

The remote handler:

1. builds role-ordered messages from current prompt, system prompt, and history;
2. applies the local tokenizer chat template;
3. wraps the token IDs in an inference request;
4. posts to the configured stream endpoint as server-sent events; and
5. decodes integer token chunks locally with the tokenizer.

Do not call the stream endpoint for a mere syntax check. Use backend-protocol's
request-preview script first.

## UI service risks

The server launch can use a broad bind address and optional share link. Treat
that as public service exposure. Always check auth flags and listen host before
recommending a launch command.
