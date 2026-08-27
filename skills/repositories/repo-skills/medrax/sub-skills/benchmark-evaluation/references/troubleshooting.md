# Troubleshooting

## Credential and endpoint failures

- **Missing `OPENAI_API_KEY`:** stop before creating a client, set it only in
  the process environment, and rerun the offline validator first. Do not put
  the key in a manifest, shell transcript, or JSONL log.
- **Custom base URL or model rejected:** verify the provider's OpenAI-compatible
  chat-completions path, multimodal message format, and exact model id. Pass
  `--model` explicitly; `OPENAI_MODEL` may not be read by the quickstart.
  Start with one case and a low temperature.
- **Authentication succeeds but vision fails:** the selected model or endpoint
  may be text-only, may reject data URLs, or may impose a different image
  limit. This is a provider compatibility failure, not evidence about the
  benchmark.

## Dataset and image failures

- **Manifest/figures mismatch:** validate `metadata.jsonl` with the bundled
  validator and use a root whose `figures/<case_id>/...` layout matches the
  manifest. The runner strips a leading `figures/` before joining its figures
  directory; avoid double `figures/figures/` paths.
- **Nested arrays or odd paths:** flatten arrays recursively, preserve order,
  normalize `figures/` and `./` prefixes, and reject traversal or URL strings
  in local mode. Run the tiny fixture checks described in the script help.
- **No-image case:** do not call the API. Record `status: "skipped"` and
  `reason: "no_images"`; investigate why the manifest has no usable image if
  the case was expected to be evaluable.
- **URL/network failure:** URL mode downloads each image before inference. A
  failed URL can leave no images or a partial image set. Confirm authorization,
  connectivity, and URL access policy; do not loop indefinitely or scrape new
  data as an implicit fix. Prefer local images for reproducible smoke tests.

## Provider and runtime failures

- **Rate limit, timeout, or transient 5xx:** the reference request retries up
  to three attempts with exponential waiting. If it still fails, preserve the
  error record and classify the case as errored. Reduce `--max-cases`, request
  rate, or provider concurrency outside this skill; never add unbounded retry.
- **Rate limit after partial run:** do not count missing lines as wrong answers.
  Record the completed prefix and rerun with a new log prefix and an explicit
  non-overlapping slice if the runner supports it.
- **Unexpected answer text:** retain the raw `model_answer`; calculate a
  normalized choice only in a separate, documented analysis. Do not modify the
  model response in the raw log.
- **SIGINT/SIGTERM:** the shutdown event is checked between cases, not a hard
  cancellation of the current request. Keep the partial log and mark the run
  interrupted. A restart may duplicate the last in-flight case, so deduplicate
  by `question_id` during analysis.

## Logging and interpretation

- **Permission or disk error:** choose a writable non-sensitive log prefix,
  ensure the parent exists, and verify the file is non-empty. Do not use a
  privileged command to hide an incorrect output directory.
- **Log contains image data:** the reference implementation may retain
  multimodal `messages`, including base64 data URLs. Treat that raw file as
  private; make a redacted copy that removes image payloads and sensitive case
  text before sharing.
- **Dataset accuracy looks low/high:** first check answer parsing, image
  availability, model/provider version, prompt contract, case ordering,
  temperature, and skipped/error denominators. Benchmark accuracy is not
  clinical validation and cannot establish diagnostic safety.
