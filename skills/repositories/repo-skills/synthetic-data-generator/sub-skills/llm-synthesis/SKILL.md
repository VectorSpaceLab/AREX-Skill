---
name: llm-synthesis
description: "Use SDGX SingleTableGPTModel for OpenAI-compatible tabular
  generation, metadata-only synthesis, raw-data prompting, off-table features,
  and offline response parsing."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SDGX LLM Synthesis

Use this sub-skill when the task mentions `SingleTableGPTModel`, OpenAI/GPT tabular synthetic data, metadata-only generation without real rows, off-table feature inference, response parsing, `OPENAI_KEY`, or `OPENAI_URL`.

Use [../single-table-synthesis/SKILL.md](../single-table-synthesis/SKILL.md) for CTGAN/GaussianCopula or CLI fit/sample workflows. Use [../data-preparation/SKILL.md](../data-preparation/SKILL.md) first when the metadata itself is the blocker.

## Safe workflow

1. Confirm the user permits sending the relevant table content or metadata to the configured LLM endpoint.
2. Inspect settings without exposing secrets:
   ```bash
   python sub-skills/llm-synthesis/scripts/inspect_llm_settings.py --json
   ```
3. Prepare either raw rows, a `DataLoader`, or a `Metadata` object.
4. Instantiate `SingleTableGPTModel`, set `dataset_description` and `off_table_features` if needed, and call `fit(...)`.
5. Set OpenAI-compatible settings via environment variables or `set_openAI_settings`.
6. Call sample/generation methods only after `check()` can pass.
7. Validate parsed samples: shape, columns, off-table columns, and values that should remain categorical or numeric.

Read [references/gpt-model-workflow.md](references/gpt-model-workflow.md) for API details and offline parsing patterns.

## Key properties

- Default `openai_API_url`: `https://api.openai.com/v1/`.
- Default `gpt_model`: `gpt-3.5-turbo` in the inspected source.
- Default `max_tokens`: `4000`; `temperature`: `0.1`; `timeout`: `90`; `query_batch`: `30`.
- `OPENAI_KEY` and `OPENAI_URL` are read from the environment at initialization.
- `off_table_features` can request new columns inferred from existing rows/metadata.

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for missing API keys, base URL mistakes, token limits, raw-data privacy, response parsing, and off-table feature failures.
