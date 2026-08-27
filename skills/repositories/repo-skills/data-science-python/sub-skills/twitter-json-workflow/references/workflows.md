# Workflows

## 1) Offline JSONL extraction

1. Use `scripts/extract_tweet_text.py` on one or more JSONL files.
2. Leave `--field` unset for the default `extended_tweet.full_text -> full_text -> text` precedence, or repeat `--field` to override the search order.
3. Choose `--format text` for newline-safe text export or `--format jsonl` for a structured line per tweet.
4. Treat malformed lines as data-quality noise: by default the script warns and continues; use `--on-error stop` only when you need strict validation of the archive.
5. The script uses stdlib `json` only; it does not require R or a third-party JSONL reader.

Example:

```bash
python scripts/extract_tweet_text.py tweets.jsonl > tweets.txt
python scripts/extract_tweet_text.py tweets.jsonl --format jsonl \
  --field extended_tweet.full_text --field full_text --field text \
  > tweets.cleaned.jsonl
```

## 2) Optional live-stream planning

1. Fill the expected Twitter/X credential environment variables locally before attempting a connection.
2. Run `python scripts/twitter_stream_template.py --track ...` first without `--connect`.
3. Review the dry-run output: it should list the planned terms, chosen output target, and missing credentials.
4. Only when you are ready to connect, add `--connect`.
5. Use the template as a starting point for an external collector if you need retries, persistence, or rule management beyond this sub-skill.

Example:

```bash
python scripts/twitter_stream_template.py --track python data
python scripts/twitter_stream_template.py --track python data --connect
```

## 3) Hand-off guidance

- Keep extracted text separate from downstream sentiment or topic modeling code.
- When the goal is model-building rather than extraction, hand the cleaned text to the next workflow instead of extending this sub-skill.
