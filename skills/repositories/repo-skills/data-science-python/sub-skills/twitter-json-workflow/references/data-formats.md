# Data formats

## Input

- One JSON object per line.
- Valid inputs often come from Twitter/X API archive dumps, file-based exports, or stream captures.
- The extractor accepts these text-bearing fields by default:
  - `extended_tweet.full_text`
  - `full_text`
  - `text`
- You can also pass any custom dotted path with `--field`.
- Nested list indexes are supported in dotted paths for simple cases such as `entities.hashtags.0.text`.
- If multiple candidate fields are given, the first non-empty value wins.
- For nested retweets or quotes, pass the exact dotted path you want with `--field`.

## Text field precedence

1. `extended_tweet.full_text`
2. `full_text`
3. `text`
4. Any user-supplied `--field ...` order

If a record has no usable text, the extractor skips it and reports a count.

## Output: text mode

- One tweet per line.
- Embedded line breaks are normalized to spaces so the output remains line-oriented.
- Best for word counts, tokenization, or feeding simple NLP pipelines.

## Output: jsonl mode

Each output line is a JSON object with at least:

- `text`
- `text_field`
- `source_file`
- `source_line`

When present, the extractor also carries through useful metadata such as:

- `tweet_id`
- `created_at`
- `lang`

Use this mode when you want provenance or need to rejoin the extracted text with other metadata later.

## Live-stream output

- The live-stream template writes raw tweet JSON lines, not model features.
- That raw archive can be fed back into `scripts/extract_tweet_text.py` later.

## What is intentionally out of scope

- Sentiment labels, topic models, and classifiers
- Feature engineering for text classification
- Any training or evaluation logic
