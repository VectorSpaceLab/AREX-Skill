---
name: "tokenization"
description: "Routes GPT2-Chinese tokenizer selection, vocabulary rebuilding,
  and BERT, word-level, or BPE setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tokenization

Use this sub-skill when the task is about choosing, inspecting, or rebuilding the tokenizer and vocabulary stack for GPT2-Chinese.

## Read first

- `../references/workflows.md` for the tokenizer-related end-to-end flow.
- `../references/data-formats.md` for corpus and vocabulary file shapes.
- `../references/model-overview.md` for matching a tokenizer to a model config.
- `../references/cli-reference.md` for the CLI flags that switch tokenization modes.
- `../references/troubleshooting.md` and this sub-skill's troubleshooting file for path and dependency failures.
- `scripts/build_vocab.py` in this sub-skill when you need a safe vocabulary builder.

## What belongs here

- The default character/BERT tokenizer in `tokenizations/tokenization_bert.py`.
- The word-level tokenizer in `tokenizations/tokenization_bert_word_level.py`.
- The BPE helper in `tokenizations/bpe_tokenizer.py`.
- Vocabulary bundles such as `cache/vocab_small.txt`, `cache/vocab.txt`, `cache/vocab_seg.txt`, `cache/vocab_all.txt`, and `cache/vocab_guwen.txt`.
- Rebuilding a vocabulary from a JSON corpus.

## What does not belong here

- Training schedules, checkpoints, or perplexity evaluation belong in training.
- Prompted generation belongs in generation.
- Generic tokenizer theory without this repo's files and vocab bundles belongs elsewhere.

## How to route a tokenizer request

1. Decide whether you need the default path or an alternate tokenizer.
   - Default char/BERT mode: the usual choice.
   - Word-level mode: choose when segmentation matters more than raw character pieces.
   - BPE mode: choose when you already have encoder and merge files for a subword setup.
2. Match the vocabulary to the model.
   - Keep `--tokenizer_path` aligned with `config/model_config*.json` `vocab_size`.
   - Use `cache/vocab_small.txt` with the compact smoke config.
3. Decide whether you need a fresh vocabulary.
   - Use `scripts/build_vocab.py` for a safe corpus-to-vocab helper.
   - Treat the legacy `cache/make_vocab.py` as historical source material, not the preferred runtime path.
4. Decide whether you need the repo dictionary path.
   - The word-level tokenizer uses `thulac` and the repo's dictionary file.
   - Path handling matters because the tokenizer loads that dictionary at import time.

## Common decision points

- If the user only needs a model smoke check, do not rebuild the vocabulary; use the bundled small vocab and the tiny config.
- If the corpus is already segmented or you care about word boundaries, use the word-level path and rebuild the vocab from that corpus.
- If the user wants to generate with `--segment`, make sure the training and generation vocab were built from the same segmentation style.
- If the task mentions BPE but the encoder and merge files are missing, stop and ask for them before promising a run.

## Output expectations

- A vocabulary file with special tokens first and corpus tokens after that.
- A tokenizer choice that matches the checkpoint and config.
- Clear notes about any word-level or BPE prerequisites that were required.
