# API Reference

## Purpose

Read this when you need the verified Python signatures behind the repo CLIs.

## Core model APIs

These calls were checked against the current checkout and installed `transformers==2.1.1` stack.

| API | Signature | Notes |
| --- | --- | --- |
| `transformers.modeling_gpt2.GPT2Config.from_json_file` | `(json_file)` | Loads a GPT-2 config from a JSON file. |
| `transformers.modeling_gpt2.GPT2LMHeadModel` | `(config)` | Builds a model from a config object. |
| `transformers.modeling_gpt2.GPT2LMHeadModel.from_pretrained` | `(path)` | Loads a saved checkpoint directory. |

## Repo module APIs

| Module | Signature | Role |
| --- | --- | --- |
| `train.build_files` | `(data_path, tokenized_data_path, num_pieces, full_tokenizer, min_length)` | Tokenizes a JSON corpus into training shards. |
| `train_single.build_files` | `(raw_data_path, tokenized_data_path, full_tokenizer, num_pieces)` | Tokenizes one long source string into shards. |
| `eval.build_files` | `(data_path, tokenized_data_path, num_pieces, full_tokenizer, min_length)` | Builds evaluation shards. |
| `generate.generate` | `(n_ctx, model, context, length, tokenizer, temperature=1, top_k=0, top_p=0.0, repitition_penalty=1.0, device='cpu', is_fast_pattern=False)` | Wrapper that chooses the fast or slow generation path. |
| `generate.sample_sequence` | `(model, context, length, n_ctx, tokenizer, temperature=1.0, top_k=30, top_p=0.0, repitition_penalty=1.0, device='cpu')` | Standard top-k/top-p sampler. |
| `generate.fast_sample_sequence` | `(model, context, length, temperature=1.0, top_k=30, top_p=0.0, device='cpu')` | Cached-past sampler used by `--fast_pattern`. |
| `generate_texts.sample_sequence` | `(model, context, length, n_ctx, tokenizer, temperature=1.0, top_k=30, top_p=0.0, repitition_penalty=1.0, device='cpu')` | Sampling helper for the batch-by-title generator. |
| `tokenizations.bpe_tokenizer.get_encoder` | `(encoder_file, bpe_file)` | Returns either an `Encoder` or `Encoder_SP` wrapper. |
| `tokenizations.tokenization_bert.BertTokenizer` | `(vocab_file, do_lower_case=True, do_basic_tokenize=True, never_split=None, unk_token='[UNK]', sep_token='[SEP]', pad_token='[PAD]', cls_token='[CLS]', mask_token='[MASK]', tokenize_chinese_chars=True, **kwargs)` | Default BERT-style tokenizer. |
| `tokenizations.tokenization_bert_word_level.BertTokenizer` | Same signature as above | Word-level tokenizer backed by `thulac`. |

## Behavior notes

- `generate.generate` returns a single generated id sequence.
- `train.py`, `generate.py`, `generate_texts.py`, and `eval.py` are CLI-first scripts, so the module functions are mainly helpers for the CLIs.
- The word-level tokenizer imports its dictionary at module load time, so path and working-directory handling matter.
- The generation helpers operate on ids, not raw strings; tokenization happens before sampling.
