# Flow Authoring Workflows

Use these workflows to choose the safest path for building, importing/exporting, validating, and running Langflow flows. Commands are generic and assume either an installed Langflow/LFX package or a Langflow checkout with commands available in the active environment.

## Choose the Workflow

| Task | Best path | Notes |
| --- | --- | --- |
| Build a new production-like flow | Visual editor first, then export JSON | The visual editor prevents many port/type mistakes. Use JSON edits for controlled changes after export. |
| Share or back up one flow | Export a single flow JSON | Exported file name is normally based on flow name. Avoid saving literal API keys. |
| Move multiple project flows | Project export/import | Project exports may be zip archives containing multiple flow JSON files. |
| Check JSON quickly without dependencies | Bundled `validate_flow_json.py` | Parses JSON and checks obvious node/edge/tweak mistakes without importing Langflow. |
| Check Langflow-specific structure | `lfx validate` | Uses installed `lfx`; can check structural levels, versions, credentials, edges, and required fields. |
| Smoke-run an offline flow | `lfx run` | Best for flows that avoid external credentials/network/GPU/local unavailable files. |
| Trigger a server-hosted flow | REST `/api/v1/run/$FLOW_ID` | Requires a running Langflow server and usually an API key. |
| Event-driven flow | REST `/api/v1/webhook/$FLOW_ID` | Requires a Webhook component; response starts background work rather than returning full output. |

## Import and Export

Exported Langflow flow JSON includes nodes, edges, metadata, and visual workspace details. Import/export can be done from the UI or through flow/project API endpoints handled by the SDK/API sub-skill.

Safe export rules:

- Do not export literal provider keys unless the recipient and storage location are trusted.
- If using global variables for keys, verify the target Langflow instance defines variables with matching names and valid values.
- Keep flow names, endpoint names, and tags meaningful; endpoint aliases are useful for stable `/run/{alias}` URLs.
- Re-run static validation after hand-editing JSON.

Safe import rules:

- Validate JSON parse and topology before upload.
- Check for missing credentials and provider-specific optional dependencies after import.
- If an imported flow came from an older Langflow version, run `lfx validate` and consider `lfx upgrade`/safe upgrade workflows before relying on it.
- Test with non-secret sample input first.

## Static Preflight

Use the bundled helper first when you need a safe, dependency-free check:

```bash
python scripts/validate_flow_json.py flow.json
python scripts/validate_flow_json.py flow.json --tweaks tweaks.json
python scripts/validate_flow_json.py flows/ --strict
```

The helper checks JSON parsing, top-level flow shape, node/edge lists, duplicate ids, missing node names/types, edge endpoints, common template shape mistakes, obvious credential fields, and tweak keys. It does not import Langflow, load components, execute graph code, call providers, or prove that a component class exists.

Use `--strict` when warnings should fail CI. Use `--json` when another script needs machine-readable diagnostics.

## `lfx validate`

`lfx validate` is the installed-package validator. It supports file and directory inputs and JSON output. Validation levels are cumulative:

- Level 1: JSON and structural keys (`id`, `name`, `data`, `data.nodes`, `data.edges`), plus orphan/unused node warnings and version mismatch warnings.
- Level 2: component existence in the installed component registry.
- Level 3: edge type compatibility.
- Level 4: required input values or incoming edges, plus visible password/secret field checks.

Fast structure-only validation:

```bash
lfx validate flow.json \
  --level 1 \
  --skip-components \
  --skip-edge-types \
  --skip-required-inputs \
  --skip-version-check \
  --skip-credentials
```

Deeper offline validation without component registry loading:

```bash
lfx validate flow.json --level 4 --skip-components --format json
```

Strict CI-style validation:

```bash
lfx validate flows/ --level 4 --skip-components --strict --format json
```

Expected exit-code pattern from tests:

- `0`: clean enough for selected checks.
- `1`: invalid flow or strict-mode warning failure.
- `2`: missing or unreadable path expansion before validation.

Use `--skip-credentials` for template libraries where missing keys are expected. Use `--skip-version-check` when validating old fixtures or cross-version exports and you only care about structure.

## `lfx run`

`lfx run` executes a Python graph script or JSON flow and returns `json`, `text`, `message`, or `result` output. It can read from a file, inline JSON, or stdin; choose exactly one source.

File path:

```bash
lfx run flow.json "hello" --no-check-variables --format json
```

Inline JSON:

```bash
lfx run --flow-json "$(cat flow.json)" --input-value "hello" --no-check-variables --format json
```

Stdin:

```bash
cat flow.json | lfx run --stdin --input-value "hello" --no-check-variables --format json
```

Useful flags:

- `--input-value`: supplies input when no positional input is used.
- `--format json|text|message|result`: controls success output shape; error output may still be JSON.
- `--session-id`: fixes chat/memory session identity for reproducible runs.
- `--check-variables/--no-check-variables`: controls environment-variable-name validation for no-op database execution.
- `--verbose`, `-vv`, `-vvv`: adds progress/debug output; avoid when a caller needs clean JSON.
- `--upgrade-flow check|safe`: use only with JSON sources when checking/upgrading component compatibility.

Starter-project tests treat missing API keys and provider failures as expected for many flows. A useful `lfx run` smoke signal is therefore: command parsing works, flow loads, and no `No module named 'langflow'`, `No module named 'lfx...'`, or component import error appears before the expected credential/provider failure.

## Server Run Endpoint

For a running Langflow server, trigger a flow by id or endpoint alias:

```bash
curl -X POST "http://LANGFLOW_SERVER_ADDRESS/api/v1/run/FLOW_ID_OR_ALIAS" \
  -H "Content-Type: application/json" \
  -H "x-api-key: LANGFLOW_API_KEY" \
  -d '{
    "input_value": "Tell me something interesting",
    "input_type": "chat",
    "output_type": "chat",
    "session_id": "demo-session",
    "tweaks": {}
  }'
```

Request parameters to know:

- `input_value`: main text/prompt.
- `input_type`: usually `chat` or `text`; match the flow input component.
- `output_type`: usually `chat`, `any`, or `debug`.
- `output_component`: optional target output component.
- `tweaks`: one-run component field overrides.
- `session_id`: chat/memory context id.
- `stream=true`: query parameter for token streaming when supported by the flow.

For request-scoped variables, pass headers named `X-LANGFLOW-GLOBAL-VAR-{VARIABLE_NAME}`. Header variables take precedence over OS environment variables for that run and are not persisted.

## Webhook Flow Pattern

Webhook flows start from a `Webhook` component. A common minimal debug flow is:

```text
Webhook -> Parser -> Chat Output
```

Use `Parser` in stringify mode when you only need to inspect the incoming payload. If the incoming request body is not valid JSON, the Webhook component wraps it in a `payload` object so it can still enter the flow as structured data.

Webhook trigger pattern:

```bash
curl -X POST "http://LANGFLOW_SERVER_ADDRESS/api/v1/webhook/FLOW_ID" \
  -H "Content-Type: application/json" \
  -H "x-api-key: LANGFLOW_API_KEY" \
  -d '{"id":"12345","name":"alex","email":"alex@example.com"}'
```

A successful webhook response indicates the background task started; it does not return the full flow output. Inspect the relevant output component or server logs to verify downstream results.

## Converting a Starter Flow to Offline Smoke

To turn a starter flow into an offline smoke case:

1. Copy the exported JSON to a scratch file.
2. Run the bundled static helper and fix duplicate ids, missing nodes/edges, and malformed tweaks first.
3. Identify provider/model/API-key components. For an offline smoke, either replace them with non-network components or expect a credential/provider failure after graph loading.
4. Keep `ChatInput` and `ChatOutput` connected for simple chat smoke tests.
5. Use `lfx validate --level 1` first; then use `lfx validate --level 4 --skip-components` for required-field and credential visibility.
6. Run `lfx run scratch-flow.json "hello" --no-check-variables --format json` and distinguish graph/load failures from expected provider credential failures.
7. Do not rely on local files referenced by File components unless the smoke case includes those files and the working directory is controlled.

For fully offline success, use components that do not call external providers, do not require a database-backed global variable, and do not require unavailable model runtimes such as PyTorch-backed transformer execution.
