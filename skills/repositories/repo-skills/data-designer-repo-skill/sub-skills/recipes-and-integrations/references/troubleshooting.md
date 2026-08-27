# Recipe and Integration Troubleshooting

## Purpose

Read this when a notebook, recipe adaptation, workflow chain, image/VLM pipeline, MCP/tool-use example, trace-ingestion plan, or Hugging Face export is blocked. For package-wide install/model/persona issues, also read the root troubleshooting reference and sibling sub-skills.

## API keys and model aliases

Symptoms:

- `data-designer agent context` reports no usable model aliases.
- A recipe names `nvidia-text`, `nvidia-reasoning`, `nvidia-vision`, `openai-text`, `openrouter-*`, or a custom alias, but preview/create cannot run.
- Config validation succeeds while `check_models`, preview, or create fails.

Likely causes:

- Default providers exist but required env vars are absent. The default provider env vars are `NVIDIA_API_KEY`, `OPENAI_API_KEY`, and `OPENROUTER_API_KEY`.
- A recipe-specific key is missing, such as `TAVILY_API_KEY` for hosted web search or `HF_TOKEN` for Hub upload.
- The model alias exists but points at a provider without an API key.

Recovery:

- Use `data-designer agent state model-aliases` or the cli-and-agent-tools sub-skill to inspect which aliases are usable.
- Stay in config-only planning if no external generation is authorized.
- For image/VLM recipes, confirm the alias generation type and provider-specific `extra_body` before running.
- Do not fabricate provider IDs or model aliases; ask the user to configure them or provide the intended model config.

## Notebook execution profiles and cache

Symptoms:

- Notebook execution passes locally but fails in docs/CI-like contexts.
- Cached notebooks do not reflect changed runtime settings.
- Repeated failures leave stale notebooks or source-side artifacts.
- Missing `jupytext` executable.

Evidence-backed behavior:

- The notebook build cache keys each notebook by source hash plus `NOTEBOOK_CACHE_CONTEXT`.
- CI separates cache by `NOTEBOOK_EXECUTION_PROFILE`.
- `NOTEBOOK_CACHE_ENABLED=0` removes `.notebook-cache` before execution.
- `NOTEBOOK_EXECUTION_ATTEMPTS` must be a positive integer.
- `NOTEBOOK_RETRY_DELAY_SECONDS` must be non-negative.
- `DOCS_JUPYTEXT` must point to an executable Jupytext binary.

Recovery:

- Do not run tutorial notebooks just to adapt a recipe; read the distilled patterns in this sub-skill.
- If execution is explicitly requested, confirm API keys, dependency groups, and cache profile first.
- Clear cache only when the user agrees or the workflow explicitly disables cache.
- If a notebook includes credentialed image/model cells, run only a config construction or a tiny preview when authorized.

## Remote model endpoints and timeouts

Symptoms:

- Slow self-hosted endpoint times out.
- vLLM/OpenAI-compatible endpoint is reachable but generation fails.
- Health checks fail for an image model configured with `skip_health_check=True`.

Likely causes:

- The recipe assumes an OpenAI-compatible endpoint URL, API key, and model ID.
- `inference_parameters.timeout` is lower than real per-request latency.
- Model-specific extra body, reasoning parser, multimodal limits, or max model length do not match the deployment.
- `skip_health_check=True` bypasses only the readiness probe; it does not guarantee execution.

Recovery:

- For slow endpoints, set a realistic timeout before preview/create.
- Probe with the smallest authorized preview.
- Keep provider-specific launch/config flags in the plan instead of running Docker or GPU services implicitly.
- Treat remote endpoint URLs and tokens as secrets in public artifacts.

## Image model `extra_body`

Symptoms:

- Image generation request is rejected by the provider.
- An OpenRouter chat-image recipe was adapted with the wrong request shape.
- Image-to-image editing ignores the source image.

Likely causes:

- Provider-specific `extra_body` keys were copied to the wrong provider.
- Tested OpenRouter image recipes expect `modalities` and `image_config`, not `generationConfig`.
- A diffusion image route was used for image-to-image editing; diffusion routes do not consume multimodal context.
- The selected model does not support image outputs or image context.

Recovery:

- For the tested OpenRouter image recipes, preserve:
  - `extra_body["modalities"] == ["image", "text"]`;
  - `extra_body["image_config"]` with `aspect_ratio` and `image_size`;
  - no `generationConfig` key.
- For other providers, use that provider's own image parameter schema.
- Use an autoregressive image model for editing/chained image context.
- Run config construction and validation before any provider call.

## Base64 image context

Symptoms:

- VLM says no image was provided.
- Base64 context raises a media-type or format error.
- Image paths from create mode fail when reused as context.
- Multi-page VLM recipes exceed prompt limits or send malformed image lists.

Likely causes:

- Base64 string includes a data URI with a media type that conflicts with `image_format`.
- `data_type=BASE64` was set without `image_format`.
- A local path was used without an artifact base path or model/server access.
- The seed column stores a JSON list but the adaptation treats it as a scalar.

Recovery:

- Store raw base64 when possible; if using explicit base64 mode, set `image_format`.
- Decode one sample image locally before preview.
- Confirm JSON arrays/list columns are intentional for multi-image/multi-page records.
- For generated image paths, keep the paths relative to the DataDesigner artifact base and use `ImageContext` auto resolution.
- For URL media, confirm the provider can fetch the URL and the user permits network access.

## MCP servers and tool use

Symptoms:

- Tool-augmented columns fail with missing tool alias or provider.
- Local stdio MCP server does not start.
- Hosted search tool fails authentication or times out.
- Tool loop runs too long or returns no final answer.

Likely causes:

- `ToolConfig` references a tool alias not registered with the `DataDesigner` instance.
- `allow_tools` names do not match the server's actual tools.
- Local stdio provider command/args are wrong.
- Hosted MCP endpoint key is missing, such as a Tavily URL without `TAVILY_API_KEY`.
- `max_tool_call_turns` or `timeout_sec` is unsuitable for the task.

Recovery:

- Route provider/tool configuration to plugins-and-extensions.
- Use `DataDesigner.list_mcp_tool_names(provider_name)` or a CLI/tool-state check when available.
- Keep tool servers local and deterministic for dry-runs; do not hit hosted web search without explicit authorization.
- Preserve trace capture only when the user approves storing tool-call histories.

## Recipe dependencies and optional groups

Symptoms:

- A recipe import fails for `datasets`, `bm25s`, `pymupdf`, `pyarrow`, `pillow`, `mcp`, or Jupyter/Jupytext packages.
- Installing all optional groups is too broad.

Likely causes:

- Tutorial notebooks, recipe scripts, and docs tooling use optional dependency groups.
- Individual recipe files declare PEP 723 dependencies, but those are source examples, not a mandate to install everything.

Recovery:

- Install only the dependency set for the chosen recipe family.
- For config-only adaptation, avoid installing recipe runtime dependencies.
- For PDF Q&A, expect `mcp`, `bm25s`, `pymupdf`, and model-provider dependencies.
- For notebook execution, expect Jupyter/Jupytext and any notebook-specific extras such as image datasets/Pillow.
- For image/VLM dry-runs, local Python image/base64 checks may need only pandas/Pillow/pyarrow, not GPU stacks.

## Docker or GPU VLM services

Symptoms:

- Long-document VLM recipes cannot run on CPU.
- vLLM launch flags reference H100s, tensor parallelism, large context, reasoning parsers, or `--trust-remote-code`.
- OCR/VQA scripts require `--vllm-endpoint`.

Likely causes:

- The recipe assumes a local OpenAI-compatible vLLM service hosting a large VLM or reasoning model.
- Required Docker/GPU hardware is unavailable or unauthorized.
- Model-specific launch flags are not interchangeable.

Recovery:

- Mark the recipe reference-only unless the user explicitly authorizes Docker/GPU service use.
- Verify hardware, model, endpoint, API key, and launch flags outside the runtime skill tree.
- For local planning, validate seed parquet shape and image counts only.
- Do not claim full VLM recovery from CPU-only checks.

## Hugging Face tokens and Hub uploads

Symptoms:

- Hub upload fails with authentication, permission, invalid repo id, missing metadata, empty parquet folder, invalid JSON, or image upload failure.

Recovery:

- Read `huggingface-export.md`.
- Use `repo_id` in `username/dataset-name` form.
- Set `HF_TOKEN`, pass `token=...`, or authenticate with `hf auth login`.
- Verify `metadata.json`, `parquet-files/*.parquet`, optional `images/`, and optional processor outputs before upload.
- Use `private=True` for sensitive, trace-derived, image-domain, or human-review data until reviewed.

## Large or credentialed downloads

Symptoms:

- Recipe stalls on Hugging Face datasets, source PDFs, web search, remote images, or model artifact downloads.
- User asks to run a recipe that reads private assistant trace directories.

Likely causes:

- Seed preparation downloads FinePDF PDFs or public image datasets.
- MCP search hits remote services.
- Agent rollout default paths may contain private sessions.

Recovery:

- Ask before network downloads, web search, or private trace reads.
- Prefer tiny local seed fixtures for dry-runs.
- Add timeout, max-record, and max-page limits to any approved download plan.
- Record which data was downloaded or read and where it is stored.

## Workflow chaining artifacts

Symptoms:

- Review recipe refuses to run because artifacts already exist.
- Resume with reviewed artifact fails.
- Final exported output is missing or has the wrong row count.

Likely causes:

- Artifact directory is non-empty and overwrite was not approved.
- Reviewed parquet path is missing or schema-incompatible.
- `stage_output_overrides` points to the wrong stage name or path.
- Selected workflow output was confused with the stage's actual dataset path.

Recovery:

- Do not delete or overwrite artifacts without explicit approval.
- Validate reviewed parquet shape before resume.
- Keep stage names stable and document every override.
- Use `export_stage` or local export for selected outputs before Hub upload.
