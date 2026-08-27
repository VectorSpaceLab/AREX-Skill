---
name: benchmark-evaluation
description: "Run a bounded ChestAgentBench or Eurorad multimodal evaluation
  through an OpenAI-compatible chat client, with local or URL-backed images,
  manifest checks, JSONL logging, interruption handling, and cautious result
  interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Benchmark evaluation

Use this skill to evaluate a vision-capable chat model on an already prepared,
local ChestAgentBench-style manifest or Eurorad-derived case set. This is an
**evaluation runner**, not a dataset builder and not a clinical decision tool.
Route dataset scraping, question generation, and exploratory experiments to
their sibling skills. Route MedRAX agent/tool initialization to the agent/tool
runtime skill.

## Safety and scope gate

- Start with a bounded plan: select the manifest, image mode, model, output
  prefix, and a small `--max-cases` value. Treat one case as the smoke run and
  expand only after its log and image resolution are sound.
- Network access, credentials, API spend, provider-side inference, and URL image
  downloads are deferred until the user explicitly authorizes the run. A
  manifest check never needs an API key or network access.
- ChestAgentBench/Eurorad accuracy is a benchmark observation, not clinical
  validation, patient-specific advice, or evidence of deployment safety.
- Do not place API keys, bearer headers, inline base64 image payloads, or
  unredacted prompts in a report or shared log. Preserve only the redacted
  JSONL contract described in [data-formats.md](references/data-formats.md).

## Quickstart route

1. Confirm that the supplied benchmark runner exposes the flags documented in
   [cli-reference.md](references/cli-reference.md). Do not silently substitute
   a dataset-generation command.
2. Validate a local JSONL manifest and image root before any client creation:
   ```bash
   python scripts/validate_case_manifest.py cases/metadata.jsonl --root cases
   ```
   Nested image arrays are supported. Missing local images are errors; a case
   with no image references is reported as a skip candidate. Use `--help` to
   inspect all bounded-check options.
3. For a local-image smoke run, after authorization and local data readiness:
   ```bash
   python quickstart.py --model "$MODEL" --temperature 0.2 \
     --log-prefix smoke-local --max-cases 1
   ```
   The runner loads a JSONL benchmark split, creates an OpenAI-compatible
   client, embeds local images as data URLs, and logs one JSON object per case.
4. For URL-backed images, plan exactly one case first:
   ```bash
   python quickstart.py --model "$MODEL" --temperature 0.2 \
     --log-prefix smoke-url --max-cases 1 --use-urls
   ```
   URL mode still fetches and base64-embeds the images before the API call; it
   is therefore both network work and inference work. Stop if the URL fetch is
   not explicitly authorized or cannot be bounded.
5. On success, inspect the redacted log for `question_id`, `status`, answer,
   duration, usage, and image-source counts before increasing the case limit.
   Never infer benchmark quality from a single case.

## Prompt and answer contract

The multimodal request contains a medical-case preamble, the case's multiple
choice `question`, and an instruction to answer only from the supplied images
and case information. The system role asks for only one choice letter among
`A/B/C/D/E/F`. The expected answer is the manifest's `answer` field. Preserve
the model's raw answer for audit, but normalize only a separate analysis field;
do not rewrite the source answer or silently score prose as a letter.

A valid case should have a stable `question_id`, non-empty `question`, an
expected `answer`, and `images` for local mode or `image_source_urls` for URL
mode. Image fields may be a string, a list, or nested lists. Flatten them in
order and preserve that order in the log. Empty or missing images do not call
the model: record `status: "skipped"` and `reason: "no_images"`.

## Configuration and bounded execution

- `--model` is the effective request model and takes precedence over the
  runner's default. `OPENAI_MODEL` is a useful provider/configuration
  convention, but do not assume the runner reads it automatically; pass its
  value explicitly when needed.
- `OPENAI_API_KEY` is required by the reference quickstart. `OPENAI_BASE_URL`,
  when set, is passed to the OpenAI-compatible client. Use a provider's exact
  compatible endpoint and model name; a custom base URL does not make an
  incompatible model multimodal.
- Keep temperature low and record it. `--max-cases` limits the selected prefix
  of the dataset; it is not a random sample and is not a confidence interval.
- Use a writable, non-sensitive log prefix. The timestamped output filename is
  derived from the prefix and current time; check that it exists and is
  non-empty after the run.
- The reference request retries transient-looking failures up to three times
  with exponential waits (approximately 4–10 seconds between attempts). A
  final exception is logged and raised, so persistent provider errors can stop
  the loop rather than being silently counted as wrong answers.
- SIGINT/SIGTERM sets a shutdown event checked between cases. Expect the
  current request to finish or fail; interruption is not a promise to cancel a
  provider request. Keep the log as a partial run and record processed/skipped
  counts.

## Interpretation and handoff

Separate these quantities: attempted cases, successful model responses,
no-image skips, request errors, valid-choice answers, and exact answer matches.
Report the manifest version/source description, image mode, model/base-url
class (not secrets), temperature, case limit, interruption state, and log
completeness. Do not call skipped cases incorrect unless the evaluation plan
explicitly defines that policy. A benchmark score is sensitive to image
availability, prompt wording, model/version, provider behavior, and case
ordering; compare runs only when those controls are held constant.

For detailed schemas, workflows, flags, and predictable failures, read:

- [workflows.md](references/workflows.md)
- [data-formats.md](references/data-formats.md)
- [cli-reference.md](references/cli-reference.md)
- [troubleshooting.md](references/troubleshooting.md)
