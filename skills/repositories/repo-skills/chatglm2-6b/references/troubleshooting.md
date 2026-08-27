# Cross-Cutting Troubleshooting

## Install and version conflicts

- Keep `transformers==4.30.2` unless the selected remote model revision and
  source behavior have been revalidated with a newer release.
- The legacy demo uses Gradio `.style()`. A modern Gradio error such as
  `Textbox has no attribute style` means the UI dependency is too new; pin a
  compatible 3.x release or adapt the UI constructor. Run `pip check` after
  changing the environment.
- Install `fastapi`, `uvicorn`, and `sse-starlette` only for API routes; install
  `datasets`, `rouge_chinese`, `nltk`, and `jieba` for P-Tuning/evaluation.
  DeepSpeed is an optional separate dependency.

## Model and remote code

- Unknown model class or missing `chat`/`stream_chat` usually means
  `trust_remote_code=True` was omitted, model/tokenizer revisions differ, or
  the model directory is incomplete.
- Slow or failed downloads are external-data failures, not proof that the
  source scripts are broken. Prefer a complete local cache, validate files, and
  avoid starting several concurrent downloads.
- Model weights are subject to the project model license. Read
  `license-and-safety.md` before redistribution or service exposure.

## Memory and backend

- `.cuda()` failures, OOM, or an unexpectedly slow response require checking
  free VRAM, context length, KV cache, batch/concurrency, quantization support,
  and PyTorch version. A CPU smoke does not validate the CUDA path.
- MPS is a Mac-specific alternative and needs a compatible PyTorch build/local
  model path. CUDA INT4 kernels are not a universal MPS fallback.
- Multi-GPU errors often come from a wrong `num_gpus`, missing `accelerate`, or
  a device map that moves embeddings and inputs to different devices. Inspect
  the map before loading weights.

## Data and checkpoint boundaries

- Validate JSON/JSONL schemas before training or C-Eval. Missing columns,
  malformed histories, or label encoding errors are cheaper to fix on CPU than
  after a GPU allocation.
- Distinguish a P-Tuning prefix checkpoint from a full fine-tuned checkpoint.
  Prefix weights need the base model and matching `pre_seq_len`; full weights
  load directly as a model.

## Service safety

The sample APIs use wildcard CORS, no authentication, and global model state.
Treat them as local development examples. Before non-local deployment add
access control, origin policy, request limits, timeouts, logging/redaction, and
an explicit model concurrency plan.
