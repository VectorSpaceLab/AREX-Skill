# LLM advisories

The Control Plane has an LLM advisory subsystem for suggestions and
explanations. It is intentionally not an execution system.

## Safety rule

LLM output is advisory only. It may:

- read bounded dataset/run/deployment/drift context,
- call a configured provider,
- persist an `LLMConsultation` audit row,
- return `suggested_config_json`, `suggested_action`, `reasoning_summary`, and
  `risk_flags`.

It must not directly submit a Run, promote a Trial, deploy a model, delete data,
rotate credentials, execute an approval, or otherwise perform a destructive or
production side effect. The user reviews and approves; deterministic backend
routes execute.

## Provider settings

Workspace LLM configuration lives in `LLMProviderSetting` rows.

Supported provider names in the request schema:

```text
anthropic, openai, google, azure_openai, ollama, custom_openai_compatible
```

Built-in provider factories are implemented for Anthropic and OpenAI. Tests can
register a deterministic fake under every name. Other provider names require a
registered factory/plugin or compatible implementation in the installed server.

Settings endpoints:

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/workspaces/{workspace_id}/llm/settings` | Current enabled setting or `null`. |
| `PUT` | `/api/v1/workspaces/{workspace_id}/llm/settings` | Admin-gated create/update. |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/llm/settings` | Admin-gated clear; `204`. |
| `POST` | `/api/v1/workspaces/{workspace_id}/llm/test-connection` | Round-trip provider health check. |

Write body:

```json
{
  "provider": "anthropic",
  "api_key": "sk-or-provider-key",
  "base_url": null,
  "model_name": "claude-sonnet-4-5",
  "enabled": true,
  "config": {"temperature": 0.2}
}
```

Response hides the key and includes `has_api_key`. Switching providers disables
other enabled rows in the same workspace while preserving them for audit.

Secrets are encrypted with the server Fernet key (`PYCARET_SECRETS_KEY`). If the
key changes, existing encrypted provider settings will fail to decrypt and the
user must re-enter the secret.

## Provider implementations

- Anthropic: uses Claude tool-use. The provider declares a `return_advice` tool
  with the consultation output schema and reads the first `tool_use` block.
  Install the SDK with the Anthropic LLM extra when using this provider.
- OpenAI: uses structured-output JSON schema through `response_format` and
  parses the returned JSON. `base_url` supports Azure/OpenAI-compatible
  endpoints when paired with the correct provider factory.
- Fake provider: deterministic in-memory provider for tests. It returns a stable
  `LLMAdvice` shape and never makes network calls.

Every provider implements one method:

```python
complete(system: str, user: str, output_schema: dict,
         max_tokens: int = 1024, temperature: float = 0.2) -> dict
```

## `LLMRouter` flow

`LLMRouter.consult(session, ctx)` owns all advisory calls:

1. Load the first enabled `LLMProviderSetting` for the workspace.
2. Decrypt its API key.
3. Build a provider instance through the provider registry.
4. Call `provider.complete(system=..., user=..., output_schema=...)`.
5. Validate the raw dict into `LLMAdvice`.
6. Persist `LLMConsultation` with provider, model, prompt, response JSON,
   generated config JSON, latency, and error if any.
7. Raise `NoLLMConfigured` when no provider is enabled. Raise `RuntimeError`
   after persisting the audit row when provider/validation fails.

Prompt text is truncated to 20,000 characters in the audit row to keep history
bounded.

Canonical output envelope:

```json
{
  "suggested_config_json": {},
  "suggested_action": "One-line user action",
  "reasoning_summary": "Why the suggestion makes sense",
  "risk_flags": ["small_sample", "target_leakage_suspected"]
}
```

`LLMConsultation.generated_config_json` mirrors `suggested_config_json` for
indexing/convenience.

## Six advisory endpoints

| Advisory | Endpoint | Request | Context and guards | Consultation type |
|---|---|---|---|---|
| Dataset Consultant | `POST /api/v1/llm/analyze-dataset` | `{workspace_id, data_source_id, task_type_hint?}` | CSV-upload DataSources only. Reads header and 200-row profile; flags task/target/preprocessing risks. | `dataset_analysis` |
| Experiment Designer | `POST /api/v1/llm/design-experiment` | `{workspace_id, data_source_id, goal}` | CSV-upload DataSources only; `goal` must be non-empty. Suggests RunConfig-shaped setup. | `experiment_design` |
| Run Explainer | `POST /api/v1/llm/explain-run` | `{run_id}` | Run must be terminal (`succeeded`, `failed`, or `cancelled`). Includes snapshot, leaderboard, and event stream. | `run_summary` |
| Failure Debugger | `POST /api/v1/llm/debug-run` | `{run_id}` | Run must be `failed`. Includes error and event tail; suggests minimal config/data fix. | `failure_debugging` |
| Deployment Reviewer | `POST /api/v1/llm/review-deployment` | `{pipeline_id}` | Reads Pipeline metadata, origin Run snapshot/status, and leaderboard. Produces `APPROVE`, `APPROVE WITH CAVEATS`, or `DO NOT DEPLOY` style verdict. | `deployment_risk_review` |
| Drift Analyst | `POST /api/v1/llm/analyze-drift` | `{drift_report_id}` | Reads DriftReport, Deployment, and optional Pipeline. Produces `RETRAIN NOW`, `INVESTIGATE`, `MONITOR`, or `NO ACTION` style verdict. | `drift_analysis` |

History endpoints:

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/v1/workspaces/{workspace_id}/llm/consultations?limit=50` | Newest first, max 500. |
| `GET` | `/api/v1/llm/consultations/{consultation_id}` | Fetch one row after workspace access check. |

## Prompt and schema expectations

Each consultation module defines:

- `SYSTEM`: a narrow persona and constraints.
- `OUTPUT_SCHEMA`: JSON Schema matching the four-field `LLMAdvice` envelope
  with `additionalProperties: false` at the top level.
- `build_prompt(...) -> tuple[str, str]`: serializes bounded, auditable context.
- `parse_response(...)`: defensive fallback for malformed provider output
  (the router also validates with `LLMAdvice`).

Prompt builders never send raw large datasets to providers. Dataset advisories
read a 200-row sample profile with dtypes, uniqueness, null fractions, and a
few sample values.

## Adding a new advisory safely

1. Add a new consultation module with `SYSTEM`, `OUTPUT_SCHEMA`, and a bounded
   `build_prompt` function.
2. Add a Pydantic request model to the LLM schema module.
3. Add a route in the LLM API router. Use `CurrentUser`, `get_db`, and workspace
   access checks. Validate object ownership before building the prompt.
4. Call `get_router().consult(...)` with a new `consultation_type` string.
5. Persist no side effects except the consultation audit row.
6. Add TestClient coverage with `register_fake_for_tests(...)` so tests do not
   call real providers.
7. In the UI or client, render all four envelope fields and require explicit
   user action before using `suggested_config_json`.

## Failure signals

| Symptom | Meaning / fix |
|---|---|
| `400 No LLM provider configured + enabled` | Configure workspace settings and keep `enabled=true`. |
| `400 provider must be one of ...` | Request provider name is not in the allowlist. |
| `502 <Provider> SDK not installed` | Install the appropriate LLM extra/provider SDK in the server environment. |
| `RuntimeError: Could not decrypt stored secret` | `PYCARET_SECRETS_KEY` changed or was ephemeral; re-enter the provider key. |
| `400 only csv_upload data sources are supported` | Dataset and experiment design advisories currently accept uploaded CSVs only. |
| `400 run is in state ...` | Wait for terminal state before `explain-run`; use `debug-run` only for failed runs. |
| `malformed_response` in `risk_flags` | Provider returned a dict that did not validate against `LLMAdvice`; inspect the audit row and provider schema support. |
