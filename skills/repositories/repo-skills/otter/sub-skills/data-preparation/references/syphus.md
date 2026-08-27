# Syphus preflight and output reference

Syphus is the instruction-response generation workflow associated with MIMIC-IT. It builds prompts from a dataset adapter, sends chat-style messages through a LiteLLM/OpenAI-compatible completion call, formats responses, and writes JSON outputs.

This skill only covers no-network preflight and file contracts. Do not make Syphus API calls unless the user explicitly supplies credentials, prompt/query inputs, budget, and permission.

## Environment variables

Syphus reads these environment variables before querying:

| Variable | Source default | Operational note |
|---|---|---|
| `OPENAI_API_TYPE` | `local` | API type label. For Azure/OpenAI-compatible deployments, set as required by the provider. |
| `OPENAI_API_BASE` | `http://localhost:8000` | Base URL for the OpenAI-compatible endpoint. |
| `OPENAI_API_VERSION` | `2020-04-01` | API version, especially for Azure-compatible endpoints. |
| `OPENAI_API_KEY` | empty string | Required for most remote providers. A local endpoint may not require it, but verify before running. |
| `OPENAI_API_ENGINE` | `davinci` in file utilities, documented examples use chat engines | Passed as the LiteLLM `engine`/model selector. Must match the provider deployment. |

The source file utilities import `litellm.completion` at import time. If `litellm` is missing, Syphus fails before any request. The preflight script checks this explicitly:

```bash
python ../scripts/check_syphus_env.py --dataset-name video.DenseCaptions
```

## Dataset adapter ids

Syphus recognizes these adapter ids:

- `change.SpotTheDifference`
- `change.CocoSpotTheDifference`
- `video.DenseCaptions`
- `video.TVCaptions`
- `video.VisualStoryTelling`
- `3d.SceneNavigation`
- `funqa.FunQA_translation`
- `funqa.FunQA_mcqa`
- `funqa.FunQA_dia`
- `fpv.EGO4D`
- `translate.Translation`

Each adapter produces query inputs. A query input should include an `id` and `sentences` value. Prompt files should provide:

```json
{
  "system_message": "You are a helpful assistant...",
  "in_context": [
    {"role": "user", "content": "Example input"},
    {"role": "assistant", "content": "Example output"}
  ]
}
```

For assistant in-context examples, content may be a string or a list of question/answer objects; the loader converts list entries to `Prefix: text` lines.

## Query and formatting behavior

For each dataset item, Syphus constructs chat messages:

1. system message from the prompt;
2. in-context messages from the prompt;
3. a final user message from `query_input.sentences`.

For `3d.SceneNavigation`, the final prompt additionally samples candidate activities from a local candidates list and asks for three conversations. Other datasets keep the model response as a single formatted result.

The completion call uses roughly these generation settings:

- temperature `0.7`
- max tokens `3200`
- top-p `0.95`
- no explicit stop sequence
- retry sleep only when the error string contains a rate-limit message

## Output files

For a run name built from `<dataset_name>_<dataset_version>`, Syphus writes an output directory named:

```text
output_<dataset_name>_<dataset_version>/
```

Expected files:

| File | Meaning |
|---|---|
| `query_input.json` | The exact query inputs sent to the model. |
| `valid_output.json` | Formatted successful outputs. |
| `invalid_output.json` | Present only when formatting produced invalid outputs. |
| `error_messages.json` | Present only for requests that errored. |
| `meta.json` | Token counts, valid/invalid/error counts, total examples, and elapsed time. |

These outputs are not automatically in MIMIC-IT training format. A follow-up normalization step must convert generated responses into instruction JSON records with `instruction`, `answer`, `image_ids`, and `rel_ins_ids` under a top-level `data` object.

## Preflight checklist

Before any real Syphus run:

1. `litellm` imports successfully.
2. `openai` imports successfully if the selected endpoint/provider requires it.
3. All required environment variables are set for the selected provider.
4. `OPENAI_API_ENGINE` names a valid deployment/model for that provider.
5. Prompt JSON parses and contains `system_message` and `in_context`.
6. Query input JSON parses and exposes a non-empty list/object of items with `id` and `sentences`.
7. Slice limits or sample counts are set for a dry run before a full batch.
8. The user has approved budget, rate limits, and data-sharing implications.

## Failure triage

- `ModuleNotFoundError: litellm`: install the optional LiteLLM dependency in the active environment or choose a different no-network workflow. Syphus cannot query without it.
- Missing `OPENAI_API_KEY`: remote providers usually fail. Local providers may be allowed only if the endpoint is intentionally unauthenticated.
- Rate-limit errors: reduce thread count and resume from saved outputs; do not discard partial output directories.
- Malformed results: inspect `invalid_output.json` and adjust prompts/in-context examples before scaling up.
- SceneNavigation candidate errors: ensure the candidate list required by that adapter is present in the run working directory before launching.
