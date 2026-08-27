# Troubleshooting

## Credentials

- Dry run works without credentials.
- `--connect` requires these environment variables for the legacy OAuth1 stream template:
  - `TWITTER_CONSUMER_KEY`
  - `TWITTER_CONSUMER_SECRET`
  - `TWITTER_ACCESS_TOKEN`
  - `TWITTER_ACCESS_TOKEN_SECRET`
- If the template says a credential is missing, fill them in locally and re-run.
- Never hardcode secrets into the script or skill files.

## Network and rate limits

- Start in dry-run mode to confirm track terms and output path.
- If the stream disconnects with HTTP 420/429 or a similar rate-limit code, back off and retry later; the template is intentionally conservative and stops rather than looping forever.
- Firewalls, proxy restrictions, or policy blocks can look like connection failures; verify you can reach the service before assuming the script is broken.

## Tweepy versions

- The template follows the legacy `Stream`/`StreamListener` pattern because that matches the source example.
- Some installations expose different streaming classes or require a newer API path; if your installed Tweepy does not provide the legacy classes, treat the file as a template and adapt the connection block to the version you have.
- Keep the dry-run path intact even if you modernize the connection code.

## Malformed JSON

- `JSONDecodeError` usually means the line is truncated, not valid JSON, or contains non-JSON text.
- The extractor warns and continues by default. Use `--on-error stop` only when you need strict validation of the archive.
- If a source file mixes blank lines and objects, blank lines are skipped.

## Encoding and text cleanup

- Prefer UTF-8 JSONL exports.
- If the source file has a BOM or a nonstandard encoding, pass `--encoding` to the extractor.
- Tweet text with embedded newlines is flattened to a single line in plain-text mode to keep downstream NLP tools happy.

## Missing text fields

- If a record has `extended_tweet.full_text`, `full_text`, or `text`, the extractor will use the first non-empty value.
- If none of those fields are present, the record is skipped.
- For nested retweets or quotes, pass the exact dotted path you want with `--field`.
