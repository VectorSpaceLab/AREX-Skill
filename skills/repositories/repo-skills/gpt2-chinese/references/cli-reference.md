# CLI Reference

## Purpose

Read this when you need the exact command-line flags for the repo CLIs or when a user describes a workflow only by options and default paths.

## Training CLIs

### `train.py`

Main flags:

| Flag | Meaning |
| --- | --- |
| `--device` | Comma-separated CUDA device ids used to set `CUDA_VISIBLE_DEVICES`. |
| `--model_config` | GPT-2 config JSON, usually `config/model_config_small.json` or `config/model_config.json`. |
| `--tokenizer_path` | Vocabulary file path such as `cache/vocab_small.txt`. |
| `--raw_data_path` | JSON list of article strings. |
| `--tokenized_data_path` | Directory for tokenized pieces. |
| `--raw` | Build tokenized pieces before training. |
| `--epochs` | Training epochs. |
| `--batch_size` | Training batch size. |
| `--lr` | Learning rate. |
| `--warmup_steps` | Warmup steps for the scheduler. |
| `--log_step` | Loss logging frequency; must divide `--gradient_accumulation`. |
| `--stride` | Sliding window stride over tokenized ids. |
| `--gradient_accumulation` | Backprop accumulation factor. |
| `--fp16` | Enable Apex mixed precision if available. |
| `--fp16_opt_level` | Apex opt level, usually `O1`. |
| `--max_grad_norm` | Gradient clipping value. |
| `--num_pieces` | Number of corpus shards. |
| `--min_length` | Minimum article length before tokenization. |
| `--output_dir` | Directory for checkpoints. |
| `--pretrained_model` | Existing checkpoint directory used as the starting point. |
| `--writer_dir` | TensorBoard log directory. |
| `--segment` | Use the word-level tokenizer implementation. |
| `--bpe_token` | Switch to the BPE tokenizer path. |
| `--encoder_json` | BPE encoder JSON. |
| `--vocab_bpe` | BPE merge file. |

### `train_single.py`

This is a simplified variant for one long source document. It keeps the main training flags but skips the BPE-specific options and the article-length filter.

## Evaluation CLI

### `eval.py`

Main flags:

| Flag | Meaning |
| --- | --- |
| `--device` | CUDA device ids. |
| `--model_config` | GPT-2 config JSON. |
| `--tokenizer_path` | Vocabulary file path. |
| `--raw_data_path` | Evaluation corpus JSON list. |
| `--tokenized_data_path` | Tokenized evaluation directory. |
| `--raw` | Build tokenized evaluation pieces first. |
| `--batch_size` | Evaluation batch size. |
| `--log_step` | Print frequency for perplexity. |
| `--stride` | Window stride. |
| `--num_pieces` | Number of evaluation shards. |
| `--min_length` | Minimum article length before tokenization. |
| `--pretrained_model` | Trained checkpoint directory. |
| `--output_dir` | Where to place the evaluation result file. |

## Generation CLIs

### `generate.py`

Main flags:

| Flag | Meaning |
| --- | --- |
| `--device` | CUDA device ids. |
| `--length` | Number of new tokens to sample. |
| `--batch_size` | Sample grouping used by the outer loop. Keep it at `1` unless you know why you want more. |
| `--nsamples` | Number of samples to emit. Keep it divisible by `--batch_size`. |
| `--temperature` | Sampling temperature. |
| `--topk` | Top-k filtering. |
| `--topp` | Top-p / nucleus filtering. |
| `--model_config` | Config JSON. |
| `--tokenizer_path` | Vocabulary file. |
| `--model_path` | Checkpoint directory loaded with `from_pretrained`. |
| `--prefix` | Prompt text, typically beginning with `[CLS]`. |
| `--no_wordpiece` | Parsed by the CLI but not used in the current code path. |
| `--segment` | Word-level tokenizer path. |
| `--fast_pattern` | Use cached-past decoding. |
| `--save_samples` | Save output text to `samples.txt`. |
| `--save_samples_path` | Output directory for saved samples. |
| `--repetition_penalty` | Penalty applied to repeated token ids. |

### `generate_texts.py`

This is the batch-by-title generator. Its main flags are the same generation controls plus:

| Flag | Meaning |
| --- | --- |
| `--save_path` | Directory for `<title-index>-<article-index>.txt` files. |
| `--articles_per_title` | Number of articles per title. |
| `--titles` | Space-separated title list. |
| `--titles_file` | Optional file with one title per line. |

## Helper CLIs

### `scripts/check_install.py`

Use this bundled helper to confirm imports, a tiny model instantiation, tokenizer smoke checks, and a one-step generation smoke.

### `sub-skills/tokenization/scripts/build_vocab.py`

Use this bundled helper to build a fresh vocabulary from a JSON list of strings without relying on the legacy keras-based script.
