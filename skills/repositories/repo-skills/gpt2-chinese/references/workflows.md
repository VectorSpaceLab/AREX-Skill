# Workflows

## Purpose

Read this when you need an end-to-end recipe for training, perplexity evaluation, generation, or tokenizer setup in GPT2-Chinese.

## Quick smoke check

Before using any workflow on a new checkout, run the bundled install smoke helper and confirm that the tiny model config can be loaded.

## Training from a JSON corpus

Use `train.py` when your corpus is a JSON list of article strings.

Recommended baseline:

```bash
python train.py \
  --raw \
  --model_config config/model_config_small.json \
  --tokenizer_path cache/vocab_small.txt \
  --raw_data_path data/train.json \
  --tokenized_data_path data/tokenized/ \
  --output_dir model/
```

What happens:

- `--raw` tokenizes the JSON corpus into `data/tokenized/tokenized_train_*.txt`.
- Each piece is filtered by `--min_length` before tokenization.
- Training runs with GPT-2 language-model loss and saves checkpoints after each epoch.
- The final checkpoint is written to `output_dir/final_model`.

Useful choices:

- Use `config/model_config_test.json` for fast smoke checks.
- Use `config/model_config_small.json` with `cache/vocab_small.txt` for the usual compact setup.
- Use `--pretrained_model` to continue from an earlier checkpoint directory.
- Use `--segment` only when you want the word-level tokenizer path.
- Use `--bpe_token` together with `--encoder_json` and `--vocab_bpe` for BPE mode.

### Single-corpus training

Use `train_single.py` when the source text is one long concatenated document rather than a list of separate articles.

Differences from `train.py`:

- It skips the `min_length` filter.
- It tokenizes a single joined string and slices it into training pieces.
- It is the right choice for long novels or other one-document corpora.

## Perplexity evaluation

Use `eval.py` when you want a perplexity estimate for a trained checkpoint.

Recommended baseline:

```bash
python eval.py \
  --pretrained_model model/final_model \
  --model_config config/model_config_small.json \
  --tokenizer_path cache/vocab_small.txt \
  --raw_data_path data/eval.json \
  --tokenized_data_path data/tokenized_eval/ \
  --output_dir eval_result/
```

Notes:

- `eval.py` uses the same corpus preprocessing style as training.
- The current script only writes `result.txt` when the output directory already exists, so create it first if you want a persisted score file.
- The printed perplexity is useful even when you skip writing a file.

## Text generation

Use `generate.py` for interactive sample generation and `generate_texts.py` for batch output by title.

Single-sample generation:

```bash
python generate.py \
  --model_path model/final_model \
  --model_config config/model_config_small.json \
  --tokenizer_path cache/vocab_small.txt \
  --prefix "[CLS]最美的不是下雨天" \
  --length 80 \
  --nsamples 1 \
  --batch_size 1 \
  --fast_pattern
```

Batch generation by titles:

```bash
python generate_texts.py \
  --model_path model/final_model \
  --model_config config/model_config_small.json \
  --tokenizer_path cache/vocab_small.txt \
  --titles "萧炎 江湖" \
  --articles_per_title 2 \
  --save_path generated/
```

Generation rules that matter:

- The usual checkpoints expect a `[CLS]`-prefixed prompt.
- `generate.py` and `generate_texts.py` are configured for a single decoded sample at a time; keep `--nsamples` divisible by `--batch_size` if you change the batch size.
- `--fast_pattern` uses cached past state and is the preferred smoke path.
- `--save_samples` writes `samples.txt` under the path you pass.

## Tokenizer and vocabulary setup

Use the tokenizer sub-skill when you need to choose among:

- the default character/BERT tokenizer
- the word-level tokenizer backed by `thulac`
- the BPE tokenizer backed by `encoder.json` and `vocab.bpe`

Use the bundled vocabulary helper before the word-level tokenizer if you need a fresh corpus-specific vocabulary.

The practical rule is simple: the tokenizer path, vocabulary file, and `model_config*.json` `vocab_size` should agree.
