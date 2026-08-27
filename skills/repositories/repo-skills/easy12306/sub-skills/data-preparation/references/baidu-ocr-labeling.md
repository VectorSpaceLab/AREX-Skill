# Baidu OCR-Assisted Text Labeling

The OCR helper is credentialed, networked, and unsafe to import as-is. Treat it as a reference workflow only.

## Import-time hazard

The source helper defines placeholder credentials and then evaluates a token request at module import time:

```python
AK = 'unknown'
SK = 'unknown'
TOKEN = get_token(AK, SK)
```

Importing that module can make an outbound request immediately and fail before any caller can provide real credentials. Do not import it in diagnostics, tests, or ordinary data-preparation scripts.

## Reference OCR flow

The intended workflow was:

1. Load prompt-text crops from the local `data.npz` preprocessing artifact.
2. For each crop, encode it as JPEG bytes.
3. Send it to Baidu OCR `general_basic` with an access token.
4. Read the first returned word.
5. Log `index word` rows for manual review.
6. Map reviewed words back to the 80-row label vocabulary.

## Safe replacement requirements

If a future task needs OCR-assisted labeling, build a new explicit wrapper rather than reusing the import-time-token module:

- Read credentials from environment variables or a secrets manager; never hard-code or write them into skill files.
- Fetch tokens only inside a user-invoked function or CLI command.
- Require an explicit `--allow-network` style opt-in.
- Accept pre-cropped `(19, 57)` prompt images or a validated `data.npz`.
- Log OCR suggestions separately from accepted labels.
- Require manual review before using labels for model training or hash aggregation.
- Validate final labels against the 80-row vocabulary documented by the integrated root skill.

## Failure modes to expect

- Placeholder credentials return authentication errors.
- Network calls fail, time out, or hit quota/rate limits.
- OCR can return multiple words, no words, or labels outside the vocabulary.
- Crops with wrong geometry produce low-quality OCR and should be rejected before the network call.
