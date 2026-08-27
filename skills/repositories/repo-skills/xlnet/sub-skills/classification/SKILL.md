---
name: classification
description: "Construct and adapt XLNet run_classifier.py classification and
  regression workflows for processor-backed tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XLNet classification/regression sub-skill

Use this sub-skill when the task is to fine-tune, evaluate, or generate predictions with XLNet's processor-backed `run_classifier.py` workflow.

## Best-fit tasks

- GLUE MNLI matched and mismatched classification with `task_name=mnli_matched` or `task_name=mnli_mismatched`.
- GLUE STS-B sentence-pair regression with `task_name=sts-b` and `--is_regression=True`.
- IMDB binary sentiment classification with `task_name=imdb`.
- Yelp-5 review classification with `task_name=yelp5`.
- Similar classification/regression jobs after reshaping data to one of the supported processor layouts or adding a new processor in the caller's working copy.

## Route elsewhere

- SQuAD span question answering belongs in `../squad-qa/`.
- RACE multiple-choice reading comprehension belongs in `../race-reading-comprehension/`.
- Direct XLNet graph/model API work, new losses, custom classifier heads, tokenizer internals, or checkpoint surgery belongs in `../model-api/`.

## Operating procedure

1. Identify the task processor and raw data layout in [references/data-formats.md](references/data-formats.md). Do not assume arbitrary TSV columns are configurable: the built-in processors hard-code filenames, columns, and labels.
2. Separate the runtime paths before generating a command:
   - `data_dir`: raw GLUE/IMDB/Yelp data.
   - `output_dir`: generated TFRecord cache.
   - `model_dir`: fine-tuned checkpoints and TensorFlow event files.
   - `init_checkpoint`: released or already fine-tuned checkpoint used only to initialize variables, normally during training.
   - `predict_dir`: prediction TSV/logit JSON destination for `--do_predict=True`.
3. Use the bundled safe command generator, not a source notebook or shell snippet, to produce a command template:

   ```bash
   python scripts/build_classifier_command.py --help
   ```

   The generator prints a `python run_classifier.py ...` command and never downloads data, launches training, or opens checkpoints.
4. Apply the task-specific workflow guidance in [references/workflows.md](references/workflows.md). For STS-B, keep regression mode enabled in every train/eval/predict command.
5. Check CLI semantics in [references/cli-reference.md](references/cli-reference.md), especially GPU/TPU flags, per-GPU `train_batch_size`, `eval_all_ckpt`, and prediction outputs.
6. Before running an expensive job, review [references/troubleshooting.md](references/troubleshooting.md) for stale TFRecord caches, missing model artifacts, bad dataset layout, GPU memory limits, TPU/GCS path mismatches, and multi-GPU eval pitfalls.

## High-signal guardrails

- Supported `task_name` values in this sub-skill are exactly `mnli_matched`, `mnli_mismatched`, `sts-b`, `imdb`, and `yelp5`.
- `sts-b` is regression. Always pass `--is_regression=True`; evaluation sorts by `eval_pearsonr` instead of `eval_accuracy`.
- Multi-GPU training uses TensorFlow `MirroredStrategy`; in this codebase, `train_batch_size` is per GPU, not global.
- Evaluate on one GPU unless the caller has intentionally audited sharding. The original workflow separates multi-GPU training from single-GPU evaluation to avoid incorrect metrics.
- Keep `model_dir` separate from the pretrained `init_checkpoint` directory. Eval-all-checkpoints should scan fine-tuned checkpoints in `model_dir`, not the released model directory.
- `output_dir` is a preprocessing cache. Change it or pass `--overwrite_data=True` when changing task data, sequence length, SentencePiece model, or regression/classification mode.
