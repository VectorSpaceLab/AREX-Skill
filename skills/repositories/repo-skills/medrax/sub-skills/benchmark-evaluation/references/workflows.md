# Bounded evaluation workflows

## 1. Preflight without network or API calls

1. Identify the manifest, its intended image mode, and the directory that
   should be the image root. Do not download figures or query a provider in
   preflight.
2. Run `python scripts/validate_case_manifest.py --help`, then validate the
   full manifest or a bounded prefix with `--max-cases 1`.
3. Resolve every local reference under the declared root. Check nested arrays,
   path normalization, and image extensions. A missing file is a data problem;
   fix or explicitly remove that case before inference.
4. Prepare a one-case plan containing model, temperature, log prefix, endpoint
   class, and whether the user authorized network/API work. The plan must say
   what happens on no-image, interruption, rate limit, and provider error.

The validator is intentionally offline. It does not import the OpenAI client,
read credentials, fetch URL references, or inspect the original dataset source.

## 2. Local-image smoke run

After explicit authorization, set `OPENAI_API_KEY` in the process environment
without echoing it. Optionally set `OPENAI_BASE_URL` for an OpenAI-compatible
provider. Choose the effective model explicitly with `--model`, then run one
case with local images and a unique log prefix. Confirm that the log is
non-empty, has exactly the expected question id, contains an attempted or skip
status, and does not expose a secret. Only then increase `--max-cases`.

The request prompt asks for a multiple-choice answer based only on the case
question and provided images. The system message requests a choice letter.
Record the raw response and compare it to the expected answer in a separate
analysis step; do not make the model's prose look like a normalized letter.

## 3. URL-image smoke run

URL mode is a separate risk profile. First confirm that each selected URL is
allowed, reachable under the user's network policy, and associated with the
intended case. Run one case with `--use-urls --max-cases 1`; this may make both
HTTP image requests and a model request. The reference image fetch has no
explicit request timeout in its URL encoding helper, so do not use URL mode
for an unattended or large run without an external timeout/supervisor.

If an image URL fails, no usable image may remain and the case should be
skipped; if the provider request fails, the runner logs an error and retries
according to its bounded retry policy. Preserve the log and classify the
failure instead of retrying indefinitely.

## 4. Graceful stop and restart

SIGINT or SIGTERM sets a shutdown event. The loop checks it between cases,
prints a saving-progress message, and leaves the current JSONL log intact. It
does not cancel an in-flight HTTP request. After stopping, record the last
observed case id and use a new log prefix for a resumed bounded slice; do not
assume the runner can resume exactly at a case boundary unless the manifest
slice is explicitly selected. Avoid merging raw logs without deduplicating
question ids.

## 5. Result review

Create a summary from JSONL only after validating that each line is an object.
Separate `ok`, `skipped`, and `error`; count exact answer matches only within
`ok` records with a known expected answer. Check for image-source and model
changes before comparing runs. Report the denominator and excluded cases.
Interpret findings as benchmark behavior under the stated setup—not as
clinical validation, diagnostic performance, or patient safety evidence.

## Deferred work

Dataset scraping, Eurorad figure download, question generation, and broad
exploratory sweeps are intentionally outside this workflow. They require a
separate plan and explicit authorization. Credentials, network calls, and
inference spend are always deferred until preflight passes.
