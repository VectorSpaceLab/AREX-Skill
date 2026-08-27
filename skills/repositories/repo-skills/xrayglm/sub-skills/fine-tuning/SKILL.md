---
name: fine-tuning
description: "Prepare and validate XrayGLM supervised multimodal fine-tuning
  data and adapter plans without starting expensive training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# XrayGLM fine-tuning

Use this sub-skill when a Researcher needs to prepare or gate supervised
image/question/answer records for XrayGLM, choose an adapter, or inspect the
distributed launcher and its runtime prerequisites. This route is deliberately
manual: **never start training by default**. A training run requires an
explicit user confirmation after the data, model checkpoint, adapter, CUDA,
NCCL, and multi-GPU/DeepSpeed gates below pass.

## Scope and safety

- Do data-contract and path checks here; general dataset acquisition,
  translation, deduplication, and record conversion belong to
  `data-preparation`.
- Do not use this route for generation or serving; those belong to `inference`.
- A CPU check can validate JSON, image readability, token-budget arithmetic,
  imports, and adapter configuration. It cannot validate real 6B training,
  CUDA memory use, NCCL collectives, or distributed DeepSpeed execution.
- Do not bundle or rewrite datasets. The validator is read-only.
- Stop rather than guessing when a required image, checkpoint, adapter backend,
  or distributed prerequisite is unavailable.

See [data-contract.md](references/data-contract.md) for the accepted records,
[training-reference.md](references/training-reference.md) for packing and
launcher mechanics, [lora-qlora-reference.md](references/lora-qlora-reference.md)
for adapter semantics, and [troubleshooting.md](references/troubleshooting.md)
for recovery actions. Run the deterministic checker with
[`scripts/validate_training_records.py`](scripts/validate_training_records.py).

## Operating procedure

1. **Freeze the input revision.** Record the JSON path, image base directory,
   model/checkpoint revision, intended adapter (`use_ptuning`, `use_lora`, or
   `use_qlora`), and the exact launcher overrides. Do not train while these are
   being inferred.
2. **Validate the records without mutation.** Run:
   ```bash
   python skills/disco/xrayglm/sub-skills/fine-tuning/scripts/validate_training_records.py \
     data.json --check-images --base-dir /path/to/image/root
   ```
   A zero exit status is required. A wrapper is only a container; its members
   still need exact non-empty string fields `img`, `prompt`, and `label`.
3. **Resolve paths from a stable base.** Relative `img` paths are resolved
   against the explicit `--base-dir`, not the caller's current directory.
   Confirm the same base directory will be used by the training process.
4. **Check packing assumptions.** Keep `image_length=32` unless the model and
   dataset packer are changed together. Keep the image placeholder sequence
   intact and verify source/target budgets; use the defaults in the reference
   as a starting point, not as a claim of fit for every record.
5. **Select one adapter deliberately.** P-Tuning adds trainable prefix
   parameters; LoRA adds low-rank matrices; QLoRA additionally replaces
   supported linear layers with 4-bit NF4 layers. `use_lora` wins over
   `use_qlora` because the source code uses `if ... elif`; do not request both.
   Combining P-Tuning with LoRA is technically possible in this code, but must
   be an explicit experiment and its checkpoint keys must be checked.
6. **Run only preflight checks first.** Confirm the intended Python 3.10
   environment, `torch 2.1.2+cu121`, SwissArmyTransformer 0.3.7, and
   DeepSpeed 0.10.3 where distributed training is intended. CUDA smoke is not
   a training proof. QLoRA is blocked if `LinearNF4` cannot actually initialize
   on CUDA; the supplied bitsandbytes 0.39.0 CPU-only/missing-libcudart
   warnings are not readiness.
7. **Review the corrected launcher template.** The checked-in shell is an
   experiment record, not a safe command to copy: its `--lora_rank 10\` line
   lacks a separating space and can concatenate the next flag. Use the
   corrected template in [training-reference.md](references/training-reference.md),
   review every path and GPU count, and preserve training as opt-in.
8. **Require explicit approval before execution.** At approval time show the
   data count, rejected records, image root, source/target lengths, adapter and
   trainable parameter policy, visible GPUs, hostfile, zero stage, precision,
   checkpoint destination, estimated budget, and stop conditions. If any gate
   is unresolved, do not invoke `deepspeed`.
9. **After an explicitly approved run, inspect before reuse.** Check exit status,
   rank logs, saved trainable keys, checkpoint completeness, and a small CUDA
   evaluation. Never overwrite the base checkpoint. Treat LoRA/QLoRA adapter
   merging as a separate, reversible operation and test the merged model before
   using it.

## Acceptance gates

- Every record is a JSON object with non-empty string `img`, `prompt`, and
  `label`; every checked image exists and is readable.
- The image token budget is consistent: 32 placeholder pad ids are inserted
  after `<img>` and are replaced by BLIP2 image embeddings at training time.
  Labels mask the complete context, including those placeholders, with `-100`.
- The source and target truncation rules and adapter choice are recorded; no
  accidental full-parameter update is allowed.
- CUDA, NCCL, GPU visibility, hostfile/DeepSpeed, precision, and checkpoint
  destinations are explicitly verified for a real run. CPU-only checks are
  reported as parser/data/adapter checks, never as 6B-training validation.
- Stop on malformed data, missing/unreadable images, broken QLoRA CUDA support,
  incompatible checkpoint keys, OOM/NCCL instability, or any unexplained
  checkpoint loss. See [troubleshooting.md](references/troubleshooting.md).
