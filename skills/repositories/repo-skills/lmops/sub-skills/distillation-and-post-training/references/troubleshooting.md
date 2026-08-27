# Distillation and post-training troubleshooting

This reference covers MiniLLM, DPKD, and Tuna issues. For shared LMOps-wide
hardware, credential, and installation boundaries, consult the parent skill's
troubleshooting reference when available at `../../references/troubleshooting.md`.

## Modified Transformers drift

MiniLLM and DPKD rely on patched Transformers behavior for tensor/model
parallelism and teacher-mixed or distillation-specific paths. Symptoms of the
wrong dependency stack include missing model-parallel helpers, unknown config
fields, checkpoint-loading branches that never trigger, and tensor-parallel
conversion imports that do not exist.

Action:

- Confirm the environment intentionally uses the compatible Transformers fork.
- Do not assume stock upstream Transformers supports these paths.
- Recheck `model-type` against the checkpoint family before retrying.

## DeepSpeed and distributed launch mismatch

Typical failures come from launcher/config disagreement rather than model
quality:

- `n-gpu`, `n-nodes`, hostfile, and launcher flags disagree.
- DeepSpeed config fp16/bf16 settings disagree with precision flags.
- ZeRO stage is too aggressive for evaluation or too weak for training.
- Gradient accumulation, micro-batch size, and global batch size were changed in
  different places.
- Model-parallel settings are enabled without converted shards.

Action: treat launcher, DeepSpeed config, and checkpoint layout as one contract.
Change them together.

## PEFT and LoRA paths

MiniLLM and DPKD can attach PEFT/LoRA adapters to student or teacher models. A
teacher PEFT setting without a teacher adapter path is incomplete.

Action:

- Check whether `peft`, `peft-path`, `teacher-peft-path`, and checkpoint names
  all refer to the same model family.
- If no PEFT is intended, remove PEFT flags rather than leaving stale paths.

## ROUGE and metric dependencies

MiniLLM and DPKD evaluation code imports ROUGE helpers and writes generation
metrics. Missing `rouge-score`, incompatible tokenizers, or malformed answer
files can break evaluation even when model loading succeeds.

Action: verify metric dependencies and generated answer files before treating a
metric failure as a model failure.

## Model and data downloads

The workflows mention public model hubs and datasets, but production runs should
not assume free or immediate downloads.

Common blockers:

- LLaMA-family checkpoints require license approval.
- Hugging Face tokens or cache directories may be missing.
- OpenWebText or instruction-response datasets may be too large for a quick run.
- Processed data paths may not match the selected model family.

Action: prefer explicit local or cached paths. When planning conversion or data
validation, use bundled helpers and avoid implicit downloads.

## Tensor-parallel size mistakes

The conversion scripts distinguish monolithic checkpoints from MP-sharded
checkpoints. Wrong source/target sizes can overwrite useful files or produce a
layout that later training cannot load.

Action:

1. Run `scripts/model_parallel_conversion_plan.py` first.
2. Confirm the `model-type` is supported by the intended MiniLLM or DPKD
   converter.
3. For 1→N, confirm a monolithic source checkpoint.
4. For N→1, confirm an `mpN` shard directory with all expected shard files.
5. For N→M, expect a merge-then-split plan and check output collisions.

## Tuna ranking schema mistakes

Tuna failures often come from schema drift rather than model code.

Common blockers:

- `output` is a string instead of a list of candidate strings.
- `score` length does not match `output` length.
- Raw contextual data uses `rank` in one place and `ranks` in another.
- `response_4`, `rank_str`, or `gpt_eval` was dropped after filtering.
- Generated records were partially written after an API retry or interruption.

Action: run `scripts/check_tuna_ranking_data.py` before training or regenerating
ranking files.

## OpenAI and GPT-4 provenance

Contextual ranking depends on OpenAI API access and a judge-model response that
both ranks the generated candidates and writes an additional reference answer.
Missing provenance changes the meaning of the data.

Action:

- Preserve `gpt_eval`, `rank_str`, the rank list, and `response_4`.
- Record the judge model name and generation settings outside the training JSON
  when available.
- If the ranking output is partial, validate the completed subset and regenerate
  missing records instead of silently training on mixed provenance.
