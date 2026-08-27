# Workflow overview

## Standard quickstart

1. Prepare parallel source/target text files.
2. Build vocabularies with `onmt_build_vocab`.
3. Train a checkpoint with `onmt_train`.
4. Translate new text with `onmt_translate`.
5. If needed, serve the model with `onmt_server` or convert/release it with the conversion tools.

## When to route where

- If the user is still shaping the dataset, consult `sub-skills/data-preparation/` first.
- If the user is tuning architecture, training schedule, checkpoint state, or training-only options, consult `sub-skills/training/`.
- If the user wants predictions, alignments, server routes, or CTranslate2 inference, consult `sub-skills/inference/`.
- If the user wants to convert external checkpoints or merge/release artifacts, consult `sub-skills/conversion/`.

## Representative workflow families

- Parallel translation fixture and vocabulary build flow
- Feature-aware corpus flow with source-side annotations
- Alignment-aware training flow
- Language-model generation flow
- Transformer baseline training flow
- Summarization training flow
- LLaMA/Vicuna-style fine-tuning and release flow

## Data and model assets to know

- Corpus and vocabulary fixtures are represented in the repo evidence and distilled into the data-preparation reference.
- Tiny model fixtures are represented in the repo evidence and distilled into the inference and conversion references.
- Server configuration examples are represented in the repo evidence and distilled into the inference reference.

## Optional advanced workflows

The repository also documents LLM-style conversion, fine-tuning, and evaluation flows based on converted checkpoints. Those are still routed through the same four sub-skills, but they need the extra dependencies and model assets listed in `references/compatibility.md`.
