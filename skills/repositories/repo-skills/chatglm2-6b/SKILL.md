---
name: chatglm2-6b
description: "Guides ChatGLM2-6B Transformers inference, local demos,
  FastAPI/OpenAI-compatible serving, C-Eval evaluation, and P-Tuning v2
  fine-tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ChatGLM2-6B

Use this repo-specific operating skill when a task names ChatGLM2-6B, the
`THUDM/chatglm2-6b` model, its legacy CLI/Gradio/Streamlit demos, its FastAPI
or OpenAI-compatible API samples, C-Eval evaluation, or the `ptuning/`
training/checkpoint workflow. This skill distills the public repository into
self-contained routes; model weights and benchmark datasets are external and
are never bundled.

## Start here

1. Identify the model source: Hub id, pinned revision, or a complete local
   model directory. Keep tokenizer and model revisions aligned.
2. Choose the route below and read its linked references before writing a
   command. Most official scripts assume CUDA and load several-billion-
   parameter weights; do not use them as cheap import checks.
3. Install the repo's runtime dependencies with the documented requirements,
   plus service or fine-tuning extras only for the selected workflow. Pin
   legacy Gradio/Streamlit versions when using the source demos; see
   [`references/model-and-environment.md`](references/model-and-environment.md).
4. Run the safe root preflight:
   `python scripts/check_installation.py --backend auto`.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) for
   cross-cutting model-cache, backend, version, license, and safety issues.

## Route by task

- **Local chat, streaming, CLI, Gradio, Streamlit, quantization, CPU/MPS,
  or multi-GPU placement:** read
  [`sub-skills/chat-and-demos/SKILL.md`](sub-skills/chat-and-demos/SKILL.md).
- **FastAPI `/` or OpenAI-compatible `/v1/chat/completions`, curl clients,
  SSE, or service deployment:** read
  [`sub-skills/api-serving/SKILL.md`](sub-skills/api-serving/SKILL.md).
- **C-Eval JSONL layout, answer extraction, or benchmark scoring:** read
  [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md).
- **P-Tuning v2, ADGEN/chat data, `torchrun`, prefix checkpoints, prediction,
  or optional DeepSpeed:** read
  [`sub-skills/ptuning/SKILL.md`](sub-skills/ptuning/SKILL.md).

When a task spans routes, start with the route that owns the artifact and
follow its explicit cross-link. For example, validate chat data in `ptuning`,
then use `chat-and-demos` to inspect a prefix checkpoint, and finally use
`api-serving` to expose the loaded model.

## Installation and verification

This repository is script-oriented rather than a Python distribution; it has
no `pyproject.toml`/`setup.py` package to install. From a checkout, install the
runtime file with a Python version supported by the selected dependency wheels:

```bash
python -m pip install -r references/runtime-requirements.txt
```

The bundled requirements file includes the base runtime plus service,
evaluation, and P-Tuning extras used by this skill. If you want a smaller
environment, install only the lines required by the selected route. The source
demos use legacy Gradio APIs; verify the version before launch and read the
environment reference rather than accepting an unbounded latest version. For
full-parameter fine-tuning, DeepSpeed is optional and must match the installed
PyTorch/CUDA stack.

The bundled `scripts/check_installation.py` checks dependency metadata, a
requested backend, and an optional local model path without downloading or
loading weights. It is a preflight, not proof that a multi-billion-parameter
model fits. Read [`references/repo-provenance.md`](references/repo-provenance.md)
before refreshing the skill against a changed checkout; the provenance file
records the source commit, dirty state, model-loading contract, and evidence
paths.

## Boundaries and safety

- Never claim a successful CPU import proves CUDA, MPS, quantization, or
  multi-GPU behavior.
- Do not download weights or external datasets from bundled diagnostic scripts.
  Acquire them through approved sources and validate local paths first.
- Treat the sample services' wildcard CORS and unauthenticated listeners as
  development defaults. Add authentication, origin controls, rate limits,
  and timeouts before non-local exposure.
- Respect the model-weight license and the safety restrictions summarized in
  [`references/license-and-safety.md`](references/license-and-safety.md).
