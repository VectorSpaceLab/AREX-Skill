---
name: data-pretraining
description: "Prepare XLNet pretraining corpora, TFRecords, and GPU/TPU command plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-pretraining

Use this sub-skill when you need to prepare XLNet pretraining data or commands:

- validate raw text or pre-tokenized integer-id corpora
- convert raw corpora into XLNet pretraining TFRecords
- build GPU or TPU pretraining command lines safely
- reason about `corpus_info.json`, `tfrecords/record_info*.json`, and filename matching

Route elsewhere when the request is about:

- downstream fine-tuning for classification, SQuAD QA, or RACE reading comprehension
- custom XLNet graph or model API details

Core contract:

- Raw text uses one sentence per line.
- An empty line marks a document boundary.
- Optional `<eop>` can appear at the end of a sentence line to mark a paragraph break.
- Pre-tokenized input uses whitespace-separated integer ids per line via `--from_raw_text=False`.
- SentencePiece is still required for preprocessing in both modes.
- Preprocessing emits `corpus_info.json` and `tfrecords/record_info*.json` alongside `.tfrecords` shards.
- Keep `task`, `num_task`, `pass_id`, `seq_len`, `reuse_len`, `bi_data`, `mask_alpha`, `mask_beta`, and `num_predict` aligned across preprocessing and training.
- TPU training is legacy TensorFlow 1.x / `tf.contrib` based and may not import in CPU-only environments.

Start here:

- [Workflow guide](references/workflows.md)
- [Data formats](references/data-formats.md)
- [CLI reference](references/cli-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Pretraining command builder](scripts/build_pretraining_command.py)
- [Text validator](scripts/validate_pretraining_text.py)
