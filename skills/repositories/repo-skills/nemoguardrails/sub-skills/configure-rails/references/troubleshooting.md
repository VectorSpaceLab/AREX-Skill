# Troubleshooting

Use this reference when a config fails to load, a rail is missing, or a validation rule blocks the configuration before runtime.

## 1. Start with the load-time summary

When a config fails, check these first:

- `colang_version`
- `models` entries and their `type`
- `rails.*.flows`
- `prompts` task names
- `api_key_env_var` values
- `config.py` sync initialization
- `import_paths`

Most config problems are caused by one of those fields being missing or mismatched.

## 2. Missing rail flow

### Symptom

You see an error like:

- `The provided input rail flow '...' does not exist`
- `The provided output rail flow '...' does not exist`
- `The provided retrieval rail flow '...' does not exist`

### Likely causes

- A flow name was mistyped.
- The `.co` file that defines the flow was not loaded.
- The config is using the wrong Colang version.
- A `main.co` / `rails.co` import was missed.

### Fix

- Make sure the flow name matches the Colang definition exactly.
- Check that the right `.co` files are under the config folder or an imported path.
- Confirm the config is using the intended `colang_version`.

## 3. Missing self-check prompt

### Symptom

You see errors such as:

- `Missing a \`self_check_input\` prompt template`
- `Missing a \`self_check_output\` prompt template`
- `Missing a \`self_check_facts\` prompt template`

### Likely causes

- The rail is enabled, but the matching prompt task is missing.
- The prompt task exists but has the wrong task name.
- A variant rail uses `$variant=...` and the matching variant prompt is missing.

### Fix

- Add the missing task to `prompts.yml` or `config.yml`.
- Match the prompt task exactly to the rail name.
- For variant rails, include the same `$variant=...` suffix in the prompt task.

## 4. Model type referenced by a rail is missing

### Symptom

You see errors like:

- `Input flow 'content safety check input' references model type 'content_safety' that is not defined in the configuration.`
- `Output flow 'topic safety check input' references model type 'topic_control' that is not defined in the configuration.`

### Likely causes

- The rail uses `$model=...`, but no matching `models.type` exists.
- The model exists under a different type name.
- The prompt task exists, but the model type does not.

### Fix

- Add the missing model type under `models`.
- Or change the rail and prompt to use the model type that actually exists.

## 5. Streaming rewrite limitation

### Symptom

You see an error like:

- `Output rails [...] rewrite the response, which streaming cannot apply with stream_first: True and context_size: ...`

### Likely causes

- An output rail rewrites the response.
- Streaming is enabled with a non-zero context window or with `stream_first: True`.

### Fix

Either:

- set `rails.output.streaming.stream_first: false` and `context_size: 0`, or
- remove the rewriting rail from the streaming configuration.

If the rail only judges content and does not rewrite it, streaming is usually fine.

## 6. Passthrough and single-call conflict

### Symptom

You see the error:

- `The passthrough mode and the single call dialog rails mode can't be used at the same time.`

### Likely causes

- `passthrough: true` is set.
- `rails.dialog.single_call.enabled: true` is also set.

### Fix

Choose one mode:

- keep passthrough and disable single-call, or
- keep single-call and disable passthrough.

## 7. Missing model API key

### Symptom

You see an error like:

- `Model API Key environment variable 'X' not set.`

### Likely causes

- `api_key_env_var` is set, but the environment variable is not exported.
- The variable is named correctly, but the shell session does not contain it.

### Fix

- Export the variable before loading the config.
- Or use `parameters.api_key` only when you intentionally want to place the key in the config.

## 8. `config.py` initialization problems

### Symptom

The config loads, but `LLMRails` initialization fails while loading custom providers or resources.

### Likely causes

- `init` is async instead of synchronous.
- Top-level imports in `config.py` fail.
- The provider or embedding class is not importable from the config folder.

### Fix

- Keep `def init(app)` synchronous.
- Move expensive work into `init` instead of module import time when possible.
- Verify any custom provider packages are installed.

## 9. Optional dependency failures

### Symptom

You see an import error for Presidio, YARA, multilingual refusal messages, or a third-party detector.

### Likely causes

- The rail family needs an optional package that is not installed.
- A provider needs a service key or endpoint.
- A remote model path or local model download is missing.

### Fix

- Install the narrow extra or package that matches the rail family.
- Add the required environment variable or endpoint.
- Re-run the config validator before trying a live request.

## 10. Tool rails are not active

### Symptom

A tool-calling config seems valid, but the tool rails do not run.

### Likely causes

- The config is using the default engine instead of IORails.
- The flow names are wrong.
- The request is not using OpenAI-style tool-call shapes.

### Fix

- Use IORails-compatible runtime setup.
- Keep the flow names exactly `tool call validation` and `tool result validation`.
- Make sure the request tool definitions follow the expected JSON-schema shape.

## 11. Colang migration problems

### Symptom

A converted config works partially, but some flows or prompts no longer behave as expected.

### Likely causes

- The migration tool converted common syntax but missed an edge case.
- The config still needs a manual review.
- A Colang 2.x file is missing the right import or `main` entry point.

### Fix

- Re-run migration with `--validate`.
- Review the generated files manually.
- Check the new flow names, prompt tasks, and imports.

## Fast checklist

When a config fails, verify these in order:

1. `models.type` exists for every `$model=...` reference.
2. Every enabled self-check rail has a matching prompt task.
3. The Colang version matches the file layout.
4. Streaming is compatible with any output rewrite rails.
5. `passthrough` and `single_call` are not both enabled.
6. Required environment variables and extras are installed.
7. `config.py` is synchronous and importable.
