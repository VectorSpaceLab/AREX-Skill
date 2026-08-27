---
name: race-reading-comprehension
description: "Operate XLNet RACE multiple-choice reading-comprehension training
  and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RACE Reading Comprehension

Use this sub-skill when the task is XLNet fine-tuning or evaluation on RACE-style multiple-choice reading comprehension: one passage, one question, and four answer candidates per example. The XLNet entry point is `run_race.py`; use the bundled command builder to create reviewed commands instead of reusing the repository shell templates directly.

## Route here for

- RACE training/evaluation with `train`, `dev`, or `test` splits.
- Middle-school-only or high-school-only RACE evaluation and filtered training.
- Choosing `max_seq_length`, `max_qa_length`, `eval_split`, `high_only`, and `middle_only` settings.
- TPU v3-8 and v3-32/pod recipes derived from the XLNet RACE templates.
- Diagnosing RACE-specific data layout, GCS/TPU setup, and batch-size confusion where one example expands to four candidate sequences.

## Route elsewhere

- Span-extraction SQuAD 1.1/2.0, `run_squad.py`, preprocessing, `predict_dir`, and threshold search: route to the `squad-qa` sub-skill through the root router.
- GLUE, IMDB, Yelp, DBpedia, Amazon, STS-B regression, and processor-backed text classification: route to the `classification` sub-skill through the root router.
- Direct XLNet model graph, config, tokenizer, and checkpoint helper APIs: route to the model/API guidance through the root router.

## Operating checklist

1. Confirm the task is RACE multiple-choice, not span QA or generic classification.
2. Read [references/data-formats.md](references/data-formats.md) and verify the `RACE_DIR/{train,dev,test}/{middle,high}/` tree plus per-file JSON schema.
3. Read [references/workflows.md](references/workflows.md) to pick one of the documented hardware profiles and decide whether split filtering should apply to training, evaluation, or both.
4. Use [scripts/build_race_command.py](scripts/build_race_command.py) to print a dry command for the selected profile; inspect paths and flags before execution in an XLNet runtime.
5. Use [references/cli-reference.md](references/cli-reference.md) for flag semantics and [references/troubleshooting.md](references/troubleshooting.md) for data, TPU/GCS, checkpoint, and memory failures.

## Critical rules

- Never set both `--high_only=True` and `--middle_only=True`; the source loader skips both levels instead of giving useful data.
- A `train_batch_size` of 1 is already four candidate sequences for one question. TPU batch sizes 8 and 32 correspond to 32 and 128 candidate sequences respectively.
- For TPU runs, keep local preprocessing inputs (`data_dir`, `spiece_model_file`, `model_config_path`) distinct from GCS outputs/checkpoints (`output_dir`, `model_dir`, and usually `init_checkpoint`).
- Do not reuse a full-RACE training TFRecord cache for filtered high-only or middle-only training; use a separate `output_dir` or `--overwrite_data=True`.
- Treat the TPU v3-8/v3-32 recipes as hardware-specific long-running workflows, not local GPU defaults.
