---
name: training
description: "Routes checkpoint training, continuation, evaluation, and
  data/vocab validation for the couplet model."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# training

Use this sub-skill when the user wants to train the couplet model, continue a
checkpoint, inspect BLEU or loss, or validate the aligned sentence-pair data
layout.

## Includes

- Building or reusing the TensorFlow training graph.
- Training from aligned input/target files.
- Continuing a checkpoint with `restore_model`.
- Evaluating against a held-out set and reading BLEU output.
- Checking the vocabulary order and the line-aligned data format.
- Running the bundled tiny smoke fixture to prove the training path works.

## Excludes

- Serving HTTP requests or starting the Flask inference wrapper.
- Ranking or post-processing generated couplets for the API.
- Generic TensorFlow advice that is not specific to this repository.

If the user wants generation or serving, route to `../inference/SKILL.md`.
If the user only needs install or dependency help, route back to the root
`references/dependencies.md` and `references/troubleshooting.md`.

## Read these files

- `../../references/model-overview.md` for the graph and module map.
- `../../references/dependencies.md` if the environment needs the verified package
  set first.
- `../../references/troubleshooting.md` for protobuf, checkpoint, and data-layout
  failures that block training.
- `references/workflows.md` for the step-by-step train/continue workflow.
- `references/data-formats.md` for the line and vocabulary layout.
- `scripts/train_couplet.py` for real training on explicit file paths.
- `scripts/train_smoke.py` for the tiny end-to-end verification fixture.

## Typical questions this route answers

- How do I train the model on my aligned couplet data?
- How do I resume training from a checkpoint?
- Why is BLEU not changing or why are some rows ignored?
- What should the vocabulary file look like?
- How can I prove the training graph still works after an environment change?

## Working pattern

1. Verify the runtime environment and install the pinned dependencies if needed.
2. Confirm the vocabulary starts with `<s>` and `</s>`.
3. Make sure input and target files are line-aligned and space-tokenized.
4. Run `scripts/train_couplet.py` for the real dataset or
   `scripts/train_smoke.py` for the bundled tiny fixture.
5. Use the checkpoint and eval output to decide whether to continue training or
   adjust the data/hyperparameters.

## High-value reminders

- `SeqReader` drops tokens that are absent from the vocabulary.
- `SeqReader.data_size` uses integer division by batch size.
- `Model.train` can restore the checkpoint when `restore_model=True`.
- `Model.eval` restores the saved checkpoint before computing BLEU.
- Changing the vocabulary order requires retraining or at least rebuilding the
  checkpoint.

## When to read the deeper references

- Read `data-formats.md` if the file layout or tokenization is unclear.
- Read `workflows.md` if you need the exact command sequence for a training
  run or continuation run.
- Read `troubleshooting.md` when TensorFlow import, checkpoint restore, or data
  alignment fails.
