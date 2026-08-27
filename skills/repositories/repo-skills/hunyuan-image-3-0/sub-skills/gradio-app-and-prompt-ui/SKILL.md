---
name: gradio-app-and-prompt-ui
description: "Route chat-UI launch, history, and import-breakage questions for
  HunyuanImage-3.0."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Gradio App and Prompt UI

Use this sub-skill for the interactive Gradio chat surface around HunyuanImage-3.0.
It is a launch, prompt-UI, and history-handling route; it is not the source of
truth for generation internals.

## When to use this route

- The user wants to start the web UI, choose a host or port, or set a local model path.
- The user wants to understand image uploads, conversation history, undo/retry, or context mode.
- The user asks whether to use the interactive UI or a reproducible CLI command.
- The user is blocked by the current launcher import failure and needs a safe fallback.

## Read first

- [App reference](references/app-reference.md) — launch contract, UI controls, prompt controls, image-history rules, and UI-vs-CLI guidance.
- [Troubleshooting](references/troubleshooting.md) — stale imports, missing model path, host/port pitfalls, and conversation edge cases.
- [Launch renderer](scripts/render_gradio_launch.py) — render a safe launch command without starting a server.
- [App import checker](scripts/check_app_imports.py) — check UI-related imports and report the known stale app imports.

## Route elsewhere when appropriate

- Use `local-inference-cli` for actual image generation commands, checkpoint selection, repeatable runs, and save-path control.
- Use `core-apis-and-architecture` for model, tokenizer, image-processor, public API, and import-path details.
- Use `prompt-and-image-conditioning` for the full prompt-mode matrix beyond the UI dropdown.
- Use `vllm-serving` for server deployment and OpenAI-compatible payloads.

## What this route covers

- The shell launch wrapper behavior, including `MODEL_ID`, `HOST`, `PORT`, and `GPUS` handling.
- The Gradio app entrypoint, launch arguments, sidebar controls, and prompt UI controls.
- Image upload handling, message-history conversion, context trimming, generated-image cache behavior, and the last-user-message rule.
- Safe preflight checks and command rendering for the UI path.
- Honest diagnostics for the current stale imports that block app startup.

## What this route does not cover

- Low-level generation internals, model architecture, sampler tuning, or quality decisions.
- vLLM server deployment or OpenAI-compatible client requests.
- Full CLI generation workflows beyond the fallback decision.

## Typical workflow

1. Decide whether the request is really interactive UI work.
2. If the user needs an interactive chat surface, read `references/app-reference.md` for the launch and history contract.
3. If the user only needs a launch plan, run `scripts/render_gradio_launch.py` to render the command and reject missing prerequisites.
4. If the user is debugging startup, run `scripts/check_app_imports.py` to verify the UI environment and confirm whether the stale import path is still present.
5. If launch remains blocked, route back to `local-inference-cli` rather than promising a healthy app.

## Key decisions

- Require a real local `MODEL_ID`; do not rely on the launcher placeholder.
- Treat `PORT=443` as a wrapper default, not always a safe host default; prefer an unprivileged port when binding fails.
- Use `single_round` history when the user wants only the latest turn plus the initial system prompt.
- Use `unlimited` history only when the user explicitly wants full conversation context.
- Uploaded files are image messages; unsupported content objects are not accepted by the app pipeline.
- A generation request must end with a user message. A history ending in assistant output must be fixed or cleared first.

## Acceptance bar for this sub-skill

- The current app failure mode is stated plainly.
- Fallback guidance to the CLI is easy to find.
- A future agent can answer launch, prompt-UI, image-history, and import-breakage questions without reopening the source checkout.
