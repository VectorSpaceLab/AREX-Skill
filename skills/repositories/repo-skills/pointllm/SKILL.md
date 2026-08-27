---
name: pointllm
description: "Guide PointLLM point-cloud language-model installation, data
  preparation, CUDA inference, two-stage training, demos, and benchmark
  evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC-SA 4.0
---

# PointLLM

Use this repo skill when a task involves PointLLM, colored point-cloud language
models, PointBERT point tokens, Objaverse 8192-point inputs, ModelNet40
zero-shot classification, PointLLM chat, the Gradio demo, two-stage training,
or the repository's benchmark evaluators.

This is an operating router, not a copy of the implementation. Read the
smallest route that owns the task and keep the original result files and
credentials auditable.

## Choose a route

- **Data and schemas** — read
  [data-preparation](sub-skills/data-preparation/SKILL.md) for Objaverse NPY
  files, instruction JSON, ModelNet `.dat` data, normalization, sampling,
  dataset classes, and the bundled local validator.
- **Chat, batch generation, or demo** — read
  [inference-serving](sub-skills/inference-serving/SKILL.md) for model/tokenizer
  registration, point-token prompts, CUDA/dtype budgets, file or object-ID
  inputs, batch-generation flags, output JSON, and Gradio operations.
- **Training** — read [training](sub-skills/training/SKILL.md) for Stage 1
  projector alignment, Stage 2 instruction tuning, dataclass flags, checkpoint
  handoff, FSDP/FlashAttention constraints, and preflight validation. It never
  launches distributed training automatically.
- **Scoring and metrics** — read [evaluation](sub-skills/evaluation/SKILL.md)
  for benchmark selection, result validation, OpenAI judging, resume files,
  cost accounting, traditional caption metrics, and invalid-response handling.

For a task spanning routes, start here, then follow the explicit sibling links.
Data preparation normally precedes inference or training; inference precedes
benchmark scoring.

## Installation and compatibility gate

PointLLM is distribution `pointllm` version `0.1.2`, imported as `pointllm`. The
repository metadata requires Python >=3.8, but the documented and inspected
baseline is Python 3.10 with torch 2.0.1 + CUDA 11.7, Transformers 4.28.0.dev0
from commit `cae78c46`, and tokenizers 0.12.1. Use an isolated environment;
do not install this legacy stack into an unrelated application environment.

From a PointLLM checkout, install the package and its declared dependencies:

```bash
pip install -e .
```

For the documented GPU baseline, install a torch/torchvision pair compatible
with the host driver before the editable package. Training's `train_mem` path
also requires a FlashAttention build compatible with that torch/Python/CUDA
combination; this is a compiled optional acceleration with no safe generic
wheel assumption. Deepspeed/FSDP are used by the Stage 2 profile. Keep
`numpy<2` with the older torch/Open3D stack, and use the legacy OpenAI client
(`openai==0.28.1`) for the source evaluator API. Do not use a modern OpenAI
client without adapting the evaluator.

Verify the environment before loading weights or data:

```bash
python -c "import torch, pointllm; print(torch.__version__, torch.cuda.is_available())"
python -m pip check
python scripts/check_env.py
```

Run that command from this generated skill directory; the bundled check is
read-only and reports package/backend facts. It does not load a checkpoint,
download data, contact OpenAI, or start a server. Read
[references/troubleshooting.md](references/troubleshooting.md) when imports,
legacy dependency pins, CUDA, or optional services fail.

## Runtime invariants

- Inference launchers call `.cuda()` and require a compatible CUDA runtime;
  this skill does not claim CPU inference.
- The normal colored input is a finite `(N, 6)` array: XYZ followed by RGB in
  `[0, 1]`, usually `N=8192`. XYZ is centered and scaled to unit maximum radius.
- Point tokens are checkpoint-configured; use the model's `point_token_len` and
  configured start/end tokens rather than hard-coding a prompt layout.
- The model context is 2048 total tokens. Point tokens consume context before
  the user's question and generated answer.
- Full checkpoints, Objaverse files, ModelNet files, and GPT judging are
  external resources. Validate paths and schemas before spending GPU, network,
  or API budget.

## Provenance and refresh

Read [references/repo-provenance.md](references/repo-provenance.md) before
assuming this route matches a changed checkout. The structured routing record
is in [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
The shared installed-package launcher is `scripts/run_installed_cli.py`; use it
from this generated skill directory for the historical chat/evaluation files.
If the source commit, package metadata, or public entry points differ, use a
refresh workflow instead of silently relying on this snapshot.

## Scope limits

This skill does not embed model weights, datasets, API keys, external services,
large benchmark outputs, or private environment paths. It does not promise
that an expensive training run, full benchmark, FlashAttention compilation,
Objaverse download, Gradio exposure, or OpenAI evaluation has succeeded merely
because the package imports.
