---
name: vllm-serving
description: "Deploy and call HunyuanImage-3.0 through the vLLM service path."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# vLLM Serving

Use this sub-skill when the user wants to run HunyuanImage-3.0 behind a
vLLM-compatible service, understand the OpenAI-style request shape, or compare
Docker and manual deployment paths.

## Route here when the request sounds like

- "How do I start the vLLM server?"
- "What model alias should the client use?"
- "How do I build the request payload for image generation?"
- "What environment variables does the vLLM launch script need?"
- "Why does the client get a connection error or model mismatch?"

## Do not use this sub-skill for

- Local single-process generation or direct `generate_image` calls. Route to
  `local-inference-cli`.
- Package architecture, tokenizer, image-processor, or model API names. Route
  to `core-apis-and-architecture`.
- Gradio UI launch and chat history behavior. Route to
  `gradio-app-and-prompt-ui`.

## Read first

1. [vLLM serving reference](references/vllm-serving.md) for the deployment contract, request shape,
   model alias rules, and Docker/manual setup split.
2. [Troubleshooting](references/troubleshooting.md) for the known failure surfaces and safe
   recovery steps.
3. [Server command renderer](scripts/render_vllm_server_command.py) to render the server command with
   the inspected environment variables and flags without starting vLLM.
4. [Payload builder](scripts/build_vllm_payload.py) to render the OpenAI-style request payload
   for the verified `image` and `auto` task shapes.

## What this sub-skill owns

- The custom vLLM branch requirement from the repo deployment notes.
- The `VLLM_ENABLE_HUNYUAN_IMAGE3_TASK` and `MULTI_MODA_SAVE_PATH` launch
  environment.
- The `vllm serve` flags used by the repo shell wrapper, including the alias
  `vllm_hunyuan_image3`.
- The Docker/manual setup split and the fact that the standard package install
  does not provide the full serving stack.
- The request payload fields built by the inspected vLLM client:
  `model`, `messages`, `max_completion_tokens`, `temperature`, `seed`,
  `chat_template`, `task_type`, and `task_extra_kwargs`.
- Client-side aliasing between the server `--served-model-name` and the
  request `model` field.
- Service-startup constraints such as branch drift, missing env vars, bad URL,
  bad alias, and client-only versus server-start expectations.

## What this sub-skill does not own

- The local inference CLI, prompt rewriting, or prompt-conditioning logic.
- The model/config/tokenizer/image-processor internals.
- The Gradio application or chatbot wiring.

## How to use it

- If the user wants a runnable server command, start with the renderer script
  and then apply the command in an environment that already has the custom
  vLLM branch and model checkpoint.
- If the user wants only the request body, run the payload builder first and
  match the `model` value to the server alias.
- If the user only needs the endpoint or alias, use the bundled references; do
  not reopen the original checkout.

## Safe-use notes

- The bundled scripts only render commands or payloads. They do not start a
  server or send network requests.
- The source client advertises more CLI labels than the safe bundled request
  contract. Treat `image` and `auto` as the verified payload shapes for this
  skill, and consult the troubleshooting reference if you need the other
  labels.
- The standard repository install alone is not enough for vLLM serving.
  Branch-specific vLLM code, the launch env vars, and the model checkpoint are
  still required.

## Cross-links

- `local-inference-cli` owns the non-vLLM generation command path.
- `core-apis-and-architecture` owns the underlying model and API names used by
  the rest of the repo.
