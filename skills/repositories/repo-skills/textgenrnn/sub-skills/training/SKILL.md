---
name: training
description: "Routes textgenrnn training, train_on_texts, train_new_model,
  train_from_file, and train_from_largetext_file workflows for fine-tuning,
  context labels, word-level inputs, and scratch architectures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# training

Use this sub-skill when the task is to train, fine-tune, resume, or debug a `textgenrnn` model.
It covers in-memory text lists, newline-delimited files, CSV-backed datasets, context labels, word-level inputs,
and single large text blocks.

## Use this route for

- Fine-tuning the bundled pretrained `textgenrnn` model on a small or medium text corpus.
- Training a fresh scratch model with custom `word_level`, `rnn_layers`, `rnn_size`, `rnn_bidirectional`,
  `max_length`, `max_words`, and `dim_embeddings` settings.
- Training from a newline-delimited file, a one-column CSV, or a two-column context CSV.
- Training on a single large text block by treating the file as one document.
- Managing `train_size`, `validation`, `dropout`, `save_epochs`, and optional `multi_gpu` acceleration.
- Verifying the saved config, vocab, and weights artifacts after a scratch training run.

## Do not use this route for

- Generation-only sampling, prefix completion, or interactive text creation. Route to `../generation/SKILL.md`.
- Embedding vectors, similarity search, PCA, or t-SNE analysis. Route to `../embedding-analysis/SKILL.md`.
- Import, TensorFlow, Keras, or setuptools compatibility failures. Use `../../references/installation-and-compatibility.md` first.

## Read first

- `references/api-reference.md` for the verified training signatures, defaults, and artifact names.
- `references/data-formats.md` for newline files, one-column CSV, two-column context CSV, single-large-text, and word-level data choices.
- `references/workflows.md` for common training and fine-tuning recipes.
- `references/troubleshooting.md` for batch-size, CSV, context, overfitting, and save-path failures.
- `../../references/model-overview.md` for architecture and config background.
- `../../references/installation-and-compatibility.md` when imports or backend setup fail.

## Skill-owned script

- `scripts/smoke_train_tiny.py` — creates a temporary tiny fixture, trains a scratch model for one epoch,
  and asserts that the config, vocab, and weights files were written.

## Operational checklist

1. Decide whether the request is fine-tuning or scratch training.
   - Use `train_on_texts` to continue from the current model.
   - Use `train_new_model` when you want a fresh vocabulary, a fresh config, or a word-level model.
2. Decide where the data comes from.
   - Use an in-memory list when the caller already has texts.
   - Use `train_from_file` for newline files, CSV files, or context-labeled CSV files.
   - Use `train_from_largetext_file` when the source file is one large document.
3. Decide whether labels are part of the dataset.
   - Pass `context_labels=[...]` with the same length as `texts` for in-memory contextual training.
   - Pass `context=True` for a two-column CSV where column 1 is text and column 2 is label.
4. Decide how much overfitting control you need.
   - Use `train_size < 1.0` to hold out validation sequences.
   - Keep `validation=True` if you want validation loss.
   - Use `dropout` sparingly; high values can hurt convergence.
5. Decide whether the run should stay tiny or produce samples.
   - Set `gen_epochs=0` and `validation=False` for smoke tests and artifact checks.
   - Increase `num_epochs`, `train_size`, or corpus size when you want real quality.

## File-format reminders

- `train_from_file(..., header=True, delim="\n", is_csv=False)` skips the first row by default.
- Set `is_csv=True` for a one-column CSV that stores texts in the first column.
- Set `context=True` for a two-column CSV with text in the first column and the context label in the second.
- `train_from_largetext_file` reads the entire file into a single-element text list and sets `single_text=True`.
- For word-level training, smaller `max_length` values usually work better than the default character-level setting.

## Output expectations

- Scratch training writes `name_config.json`, `name_vocab.json`, and `name_weights.hdf5`.
- If `save_epochs > 0`, intermediate snapshots are written as `name_weights_epoch_<epoch>.hdf5`.
- `save()` writes only the current weights file; it does not rewrite the config or vocab files.
- `load()` expects a matching weights file for the current config and vocabulary shape.

## Routing notes

- If the caller only needs to see generated samples after training, hand off to generation.
- If the caller is measuring semantic clustering or similarity, hand off to embedding-analysis.
- If the issue is an import mismatch or a bad TensorFlow stack, stop here and use the compatibility reference.
- If the user wants a lower-level model architecture explanation, use the root model overview instead.
