---
name: serving-cli
description: "Operate DataFlow CLI groups and serving backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# serving-cli

Use this sub-skill for DataFlow command routing and serving setup:

- root CLI discovery and command routing
- `dataflow init` and `dataflow init repo`
- `dataflow chat`
- `dataflow eval`
- `dataflow pdf2model` and `dataflow text2model`
- `dataflow webui`
- serving classes under `dataflow.serving`

Route elsewhere when the task is primarily about:

- operator, storage, prompt, or pipeline mechanics: `pipeline-foundations`
- text dataset generation and text-only training flows: `text-workflows`
- PDF / document / VQA / RAG workflows: `document-vision-rag`
- Ray acceleration and actor wrapping: `rayorch-acceleration`

Operating rules:

- Treat `--help` as discovery only; it should not download models or start services.
- Treat `init`, `eval init`, `pdf2model init`, and `text2model init` as setup commands that write files.
- Treat `chat`, `eval api/local`, `pdf2model train`, `text2model train`, and `webui` as side-effecting commands.
- Do not rely on `dataflow env` in a pipe or other non-TTY context; it can fail with `Errno 25`.
- Use `DF_API_KEY`, `GOOGLE_API_KEY`, and Google Vertex credentials only when the selected backend requires them.
- For backend-specific constructor facts, timeout behavior, and dependency warnings, see `references/serving-backends.md`.
- For CLI routing and side effects, see `references/cli-reference.md` and `references/evaluation-and-webui.md`.
- Use the bundled scripts to inspect CLI help and to smoke-test `APILLMServing_request` against a local OpenAI-style server.
