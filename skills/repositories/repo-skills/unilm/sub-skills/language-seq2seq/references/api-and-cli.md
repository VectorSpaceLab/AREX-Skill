# API and CLI Reference

## `s2s-ft/run_seq2seq.py`

Required training flags:

| Flag | Meaning | Validation |
| --- | --- | --- |
| `--train_file` | JSONL training file with `src` and `tgt` keys | Required; each line must be valid JSON. |
| `--model_type` | One of `bert`, `minilm`, `roberta`, `xlm-roberta`, `unilm`, `electra` | Must match the checkpoint/config/tokenizer family. |
| `--model_name_or_path` | Pretrained model shortcut or local checkpoint path | Required by native script; may trigger downloads if given a remote model name in an online environment. |
| `--output_dir` | Directory where checkpoints and cached features are written | Required; native script can resume from `ckpt-*` files. |

Common training flags:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--tokenizer_name` | Tokenizer shortcut or local vocab/tokenizer path | Use when tokenizer differs from model path, especially MiniLM local files. |
| `--config_name` | Config shortcut or local config path | Use when config differs from model path. |
| `--cache_dir` | Model/data cache directory | Avoid relying on implicit caches in reproducible runs. |
| `--cached_train_features_file` | Precomputed feature cache path | Must correspond to the same tokenizer and length settings. |
| `--max_source_seq_length` | Maximum WordPiece source length | Longer source examples are truncated. |
| `--max_target_seq_length` | Maximum WordPiece target length | Longer target examples are truncated. |
| `--per_gpu_train_batch_size` | Per-device batch size | Effective batch = GPU count × per-GPU batch × accumulation. |
| `--gradient_accumulation_steps` | Steps to accumulate before optimizer step | Increase this when reducing batch size for memory. |
| `--learning_rate` | AdamW learning rate | Base models often use higher rates than large models. |
| `--num_warmup_steps` | Linear warmup steps | Must be less than total training steps. |
| `--num_training_steps` | Total training updates | Takes priority over epoch-style planning. |
| `--fp16 --fp16_opt_level O1/O2` | Apex AMP mixed precision | Requires Apex; omit for CPU/debug or missing Apex. |
| `--target_mask_prob` | Target pseudo-mask probability | Used by UniLM2-style examples; tune by task. |
| `--lmdb_cache` | Store cached features in LMDB | Useful for large data; requires LMDB dependency. |

## `s2s-ft/decode_seq2seq.py`

Required decoding flags:

| Flag | Meaning | Validation |
| --- | --- | --- |
| `--model_type` | Tokenizer/model family | Must be in `bert`, `minilm`, `roberta`, `unilm`, `xlm-roberta`, `electra`. |
| `--model_path` | Checkpoint directory or glob | Native decoder loops over matching checkpoint directories. |
| `--tokenizer_name` | Tokenizer shortcut or local tokenizer path | Required; use the same casing/vocab as training. |
| `--input_file` | JSONL input file | Requires `src`; `tgt` may be omitted for decoding. |

Common decoding flags:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--config_path` | Optional config override | Defaults to `config.json` under checkpoint directory. |
| `--split` | Name appended to default output path | Use `validation`, `dev`, or `test` consistently with gold files. |
| `--output_file` | Explicit prediction output path | Prefer this when multiple checkpoints or custom locations are involved. |
| `--max_seq_length` | Total source-plus-target limit | Must exceed `--max_tgt_length + 2`; source budget is derived from this. |
| `--max_tgt_length` | Maximum generated target length | Native decoder rejects values too close to `--max_seq_length`. |
| `--batch_size` | Decode batch size | Reduce on out-of-memory errors. |
| `--beam_size` | Beam-search width | `--need_score_traces` requires `beam_size > 1`. |
| `--length_penalty` | Beam length penalty | XSum UniLM2 examples use nonzero penalty; many older examples use `0`. |
| `--forbid_duplicate_ngrams` | Block repeated n-grams | Pair with `--forbid_ignore_word` for punctuation. |
| `--forbid_ignore_word` | Pipe-separated ignored tokens | Examples use `.` or `.|[X_SEP]`. |
| `--min_len` | Minimum generated length | Useful for CNN/DM when very short outputs appear. |
| `--need_score_traces` | Save beam trace pickle | Only valid with `beam_size > 1`; trace files can be large. |
| `--pos_shift` | Position-shift decoding | Must match training/checkpoint assumptions. |

## `s2s-ft` evaluation scripts

| Script | Use | Typical flags |
| --- | --- | --- |
| `evaluations/eval_for_xsum.py` | XSum summaries | `--pred PRED --gold GOLD --split validation` |
| `evaluations/eval_for_cnndm.py` | CNN/DailyMail summaries | `--pred PRED --gold GOLD --split dev --trunc_len 160` |
| `evaluations/eval_for_gigaword.py` | Gigaword headlines | `--pred PRED --gold GOLD --split test` |

Evaluation scripts may use Python ROUGE by default and Perl ROUGE when `--perl` is passed. Perl ROUGE/pyrouge setup is fragile; first verify predictions and gold files have matching line counts.

## UniLMv1 legacy scripts

`biunilm/run_seq2seq.py` required and common flags:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--do_train` | Enable training | Native script requires `--do_train` or `--do_eval`. |
| `--bert_model` | BERT model name or path | Examples use `bert-large-cased`; tokenizer is loaded through legacy `pytorch_pretrained_bert`. |
| `--data_dir` | Directory containing source/target files | Defaults to `train.src` and `train.tgt` if file names are omitted. |
| `--src_file`, `--tgt_file` | Source and target file names under `data_dir` | Required when using non-default names. |
| `--output_dir`, `--log_dir` | Model and TensorBoard/log outputs | Checkpoint files are saved as `model.N.bin`. |
| `--model_recover_path` | Initial/recovered checkpoint file | Native script asserts this path exists when supplied. |
| `--config_path` | BERT config override | Use with local legacy configs. |
| `--new_segment_ids` | Expand segment embeddings for UniLM tasks | Often required by released UniLMv1 NLG commands. |
| `--tokenized_input` | Treat source/target files as whitespace-tokenized WordPieces | Use only when files are already tokenized for the matching vocab. |
| `--max_seq_length`, `--max_position_embeddings` | Total sequence length and position embeddings | Must fit checkpoint position embeddings. |
| `--max_len_a`, `--max_len_b`, `--trunc_seg`, `--always_truncate_tail` | Truncation controls | CNN/DM often reserves source/target budgets explicitly. |
| `--mask_prob`, `--max_pred` | Target masking controls | Task examples often use `0.7` and task-specific max predictions. |
| `--fp16 --amp` | Old Apex AMP path | Requires old Apex/Torch compatibility; omit for CPU inference/debug. |

`biunilm/decode_seq2seq.py` common flags:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--bert_model` | BERT tokenizer/model family | Must match checkpoint casing and vocab. |
| `--model_recover_path` | Fine-tuned `.bin` checkpoint or glob | Decoder writes default predictions as `MODEL_RECOVER_PATH.SPLIT`. |
| `--input_file` | Source file for decoding | Plain text or tokenized text depending on `--tokenized_input`. |
| `--new_segment_ids`, `--s2s_special_token`, `--pos_shift` | Special UniLM variants | Must match the checkpoint and vocab special tokens. |
| `--beam_size`, `--length_penalty`, `--forbid_duplicate_ngrams` | Search controls | `--need_score_traces` requires beam search. |

`biunilm/gen_seq_from_trace.py` can post-process `.trace.pickle` files from legacy decoding with `--alpha`, `--length_penalty`, `--expect`, or `--min_len`. It is reference-only unless trace generation was explicitly requested.

## Tokenizer and model facts

- UniLMv1 bundles a legacy `pytorch_pretrained_bert` package named version `0.4.0`; setup requirements list `numpy`, `boto3`, `requests`, and `tqdm`.
- The legacy tokenizer loads `vocab.txt`, lowercases when `do_lower_case=True`, preserves special tokens, splits punctuation/CJK characters, and uses greedy WordPiece with `[UNK]` fallback.
- Legacy model config defaults use `bert_config.json`; weights default to `pytorch_model.bin` in extracted pretrained archives.
- `s2s-ft` UniLM and MiniLM tokenizers subclass BERT tokenization and use one-token-per-line vocabulary files.
- Cased checkpoints require cased vocab/tokenizer and no `--do_lower_case`; uncased checkpoints require the lowercasing flag for parity with training.
