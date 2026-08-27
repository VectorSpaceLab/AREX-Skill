---
name: twitter-json-workflow
description: "Extract tweet text from stored Twitter/X JSONL and plan safe
  optional live streaming."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# twitter-json-workflow

Use this sub-skill for portable tweet-text extraction from stored Twitter/X JSONL and for cautious, opt-in planning around live streaming.

## Route here for

- JSONL tweet archives that need `text`, `full_text`, or `extended_tweet.full_text` extraction
- malformed-line tolerant parsing, newline-safe plain-text export, and optional JSONL output
- a dry-run first pass for Tweepy-based live capture with no hardcoded secrets
- keeping source data ready for later NLP, topic, or sentiment work

## Route elsewhere

- Sentiment modeling, classifier training, or topic analysis on the extracted text: use the tutorial-resource-map sibling for learning resources or downstream tooling for actual model work
- R/jsonlite workflows: use the bundled Python extractor instead
- Long-running production ingestion or dashboarding: use a dedicated downstream service

## Read first

- [Workflows](references/workflows.md)
- [Data formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Offline extractor](scripts/extract_tweet_text.py)
- [Live-stream template](scripts/twitter_stream_template.py)

## Quick decision map

| Need | Use |
| --- | --- |
| Convert JSONL tweets to one clean text line per tweet | `scripts/extract_tweet_text.py` |
| Preserve one output row per input tweet with lineage | `scripts/extract_tweet_text.py --format jsonl` |
| Prefer a nested field such as `extended_tweet.full_text` | `scripts/extract_tweet_text.py --field ...` |
| Dry-run a planned live stream | `scripts/twitter_stream_template.py` |
| Connect to streaming only after credentials and policy are ready | `scripts/twitter_stream_template.py --connect` |

## Typical path

1. Start with the field order and output choices in `references/data-formats.md`.
2. Run the offline extractor on a tiny JSONL sample and confirm malformed lines are reported, not fatal.
3. If live capture is needed, use the stream template in dry-run mode first and only add `--connect` once credentials and network policy are confirmed.
4. Hand extracted text off to the next analysis stage; do not use this sub-skill for model training itself.

## Example commands

```bash
python scripts/extract_tweet_text.py tweets.jsonl > tweets.txt
python scripts/extract_tweet_text.py tweets.jsonl --format jsonl > tweets.cleaned.jsonl
python scripts/twitter_stream_template.py --track python data
python scripts/twitter_stream_template.py --track python data --connect
```
