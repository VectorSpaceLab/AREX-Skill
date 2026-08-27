---
name: class-conditional
description: "Router for LlamaGen class-conditional ImageNet generation,
  training, serving, packaging, and evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# class-conditional

Use this sub-skill for LlamaGen class-conditional ImageNet workflows that do **not** require tokenizer training or text conditioning. The bundled wrappers pin `--gpt-type c2i`; use the text-conditional sub-skill for `t2i`.

## In scope
- DDP class-conditional training and resume flows.
- FSDP class-conditional training and resume flows.
- Single-process and DDP sampling.
- vLLM serving for class-conditional checkpoints.
- Packaging sample folders into `.npz` batches for evaluation.
- c2i evaluation against ImageNet reference batches.
- Model-family and checkpoint-format guidance for c2i checkpoints.

## Route elsewhere
- Tokenizer training or reconstruction -> `tokenizers`
- Preprocessing requests, including discrete-code extraction or T5 extraction -> `data-preparation`
- Text-conditional workflows -> `text-conditional`
- Publish / upload scripts -> excluded

## Start here
- `references/workflows.md` for workflow selection and checkpoint shape notes.
- `references/cli-reference.md` for exact wrapper flags and env vars.
- `references/serving.md` for vLLM path, model-id, and memory notes.
- `references/evaluation.md` for `.npz` layout and packaging expectations.
- `references/troubleshooting.md` for DDP, FSDP, vLLM, and evaluator failures.

## Bundled scripts
- `scripts/train_c2i.sh`
- `scripts/train_c2i_fsdp.sh`
- `scripts/sample_c2i.sh`
- `scripts/sample_c2i_ddp.sh`
- `scripts/sample_c2i_ddp_pack_npz.py`
- `scripts/serve_c2i_vllm.sh`
- `scripts/evaluate_c2i.sh`

## Checkpoint and model notes
- DDP training saves checkpoints with `model`, `optimizer`, `steps`, `args`, and optional `ema`.
- FSDP resume expects a directory with `consolidated.pth`, `optimizer.*.pth`, and `resume_step.txt`.
- Sampling and serving can read `model`, `module`, or `state_dict` checkpoints; raw FSDP weights need `--from-fsdp`.
- The vLLM path is wired for the class-conditional fake JSON configs only.

## Troubleshooting priorities
- Fix CUDA / NCCL / world-size mismatches first.
- Check checkpoint key shape or FSDP world-size compatibility next.
- Then check vLLM model-id paths, GPU memory sizing, and evaluator `.npz` inputs.
- Treat `app.py` as reference-only because it loads checkpoints at import time.
