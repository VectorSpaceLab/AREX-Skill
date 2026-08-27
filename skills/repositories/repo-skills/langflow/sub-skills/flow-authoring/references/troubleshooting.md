# Flow Authoring Troubleshooting

Use this guide when a Langflow flow JSON file, tweak payload, `lfx validate`, `lfx run`, REST run request, or webhook flow fails.

## Install and Import Failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `langflow: command not found` or `lfx: command not found` | Package environment is not active or commands are not installed | Activate the intended environment, install Langflow/LFX, or run commands through the environment's package runner. |
| `No module named 'langflow'` | Flow or component code expects Langflow runtime modules unavailable to the active Python | Install matching `langflow`, `langflow-base`, and `lfx` packages or run inside the project environment. |
| `No module named 'lfx...'` | Installed `lfx` package does not match flow/component code or checkout | Use a consistent Langflow/LFX version; avoid mixing old starter JSON with incompatible package code without upgrade checks. |
| `cannot import name ...` from `langflow` or `lfx` | Version skew across `langflow`, `langflow-base`, `lfx`, or extension bundles | Reinstall matching distributions and rerun `lfx validate`/`lfx run`. |
| `No module named 'langchain_core.memory'` | Incompatible `langchain-core` 1.x pulled in by dependency skew | Use compatible `langchain-core`, `langchain-openai`, and `langchain-community` versions expected by the installed LFX/Langflow release. |
| CLI import fails around `OpenAI` or voice/model modules | Optional provider dependency missing for the current import path | Install the relevant optional provider package only if that feature is in scope. |
| Transformer/model execution unavailable | Heavy ML backend such as PyTorch is not installed | Keep flow authoring checks static/offline, or install the backend only for tasks that explicitly require model execution. |

## JSON and Schema Failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `Invalid JSON` | Comments, trailing commas, bad quoting, or truncated export | Re-export or repair JSON with a strict parser before editing. |
| Missing `data.nodes` or `data.edges` | Graph-only or malformed flow shape | For exported flows, use top-level metadata plus `data: {nodes: [], edges: []}`. For graph-only fixtures, ensure root `nodes` and `edges` are lists. |
| Duplicate node id | Copied node without changing ids everywhere | Change root `id`, `data.id`, edge references, and handle payload ids consistently. |
| Edge references non-existent node | Deleted/renamed node without updating edges | Remove the edge or point `source`/`target` to existing node ids. |
| Required input warning | Field has no value and no incoming edge | Add a field value, connect an upstream component to the field, or intentionally skip required-input checks for partial drafts. |
| Type mismatch warning | Edge connects incompatible output/input port types | Reconnect compatible ports or add a conversion component such as a type-conversion/parser step. |
| Orphaned/unused node warning | Node has no edge, or no path reaches output nodes | Connect the node to the intended path, delete it, or document it as a note/debug-only artifact. |
| Old-version warning | Node `lf_version` differs from installed validator version | Run upgrade checks or validate with version warnings skipped when inspecting frozen fixtures. |

## Tweak Failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| Tweak appears ignored | Component key does not match a node id or unique display name | Use the exact node id from `data.nodes[*].id`. |
| Field tweak ignored | Field name is not in `data.node.template` | Inspect the node template and use the exact field key, not the display label. |
| Wrong node changed | Top-level field tweak applied across all matching fields | Prefer node-scoped tweaks: `{"NodeId": {"field": value}}`. |
| Code field not changed | Runtime blocks code/sandbox tweaks for safety | Edit trusted component source or flow JSON deliberately; do not use tweaks for code injection. |
| File tweak does not work | File field expects `file_path` behavior | Pass a valid path reachable from the runtime working directory, or use a dict shaped for the specific file field. |
| Nested JSON tweak fails | Value is a string that is not valid JSON | Pass a real JSON object rather than a stringified object where possible. |
| Embedded widget tweak fails | JSON prop formatting differs by framework | Use stringified JSON for plain HTML/React attributes or property binding for frameworks that pass objects. |

## CLI Misuse

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `lfx run` says no input source | No script path, `--flow-json`, or `--stdin` was provided | Provide exactly one flow source. |
| `lfx run` rejects combined sources | File path, `--flow-json`, and/or `--stdin` were combined | Choose one source mode. |
| Empty stdin error | `--stdin` used without piping content | Pipe flow JSON into the command or use a file path. |
| Error output is JSON despite `--format text` | Error handling returns a JSON envelope in some code paths | Parse errors separately from success output; avoid assuming error output follows success format. |
| Verbose mode breaks JSON parsing | `--verbose`, `-vv`, or `-vvv` adds diagnostics | Use non-verbose mode for machine-readable JSON. |
| Variable validation fails under no-op DB | Global-variable names contain spaces, hyphens, punctuation, or start with a digit | Use environment-variable-safe names such as `OPENAI_API_KEY`; or run with `--no-check-variables` for a load-only smoke. |
| `lfx validate` exits `1` with only warnings | `--strict` treats warnings as failures | Remove `--strict` for exploratory checks or fix the warnings. |
| `lfx validate` exits `2` | Input path does not exist or path expansion failed | Check the path and shell quoting. |

## API and Backend Failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| HTTP 401/403 | Missing or invalid Langflow API key | Pass `x-api-key` or create a valid key for the server. |
| HTTP 404 for flow id/alias | Wrong flow id, endpoint alias, or workspace/project visibility | Copy the id/alias from the flow URL/API access pane and verify permissions. |
| HTTP 422 | Request body shape or content type is wrong | Send JSON with `Content-Type: application/json`; verify `input_value`, `input_type`, `output_type`, and `tweaks` types. |
| Empty chat widget response | Flow lacks proper Chat Input/Chat Output path | Use a chat-compatible flow or trigger it through the API with the right input/output types. |
| Webhook returns task started but no final output | Webhook endpoint starts background work | Inspect the output component, Playground/message logs, or server logs; do not expect full output in the webhook response. |
| Missing global variable at run time | Variable not defined in Langflow database, request headers, or environment fallback | Define the variable, pass `X-LANGFLOW-GLOBAL-VAR-*` header, or configure environment fallback intentionally. |
| Network/provider timeout | Flow calls external LLM/vector/search/file service | Use provider credentials, network access, and timeouts appropriate for that component; for offline smoke, replace or skip provider components. |

## Runtime and Credential Boundaries

Many starter flows are intentionally provider-backed. Missing API keys, external network failures, rate limits, or unavailable model hardware are not necessarily flow JSON defects. For verification, separate failures into:

- Static defects: invalid JSON, missing graph arrays, duplicate ids, broken edges, invalid tweaks.
- Graph build defects: missing component type, incompatible package versions, required fields with no value/edge.
- Runtime defects: missing credentials, missing optional packages, external service failures, local file path problems, database/global-variable issues.
- Output extraction defects: flow runs but caller reads the wrong nested result field.

Use static validation to eliminate static defects before spending time on runtime failures.

## Safe Debug Sequence

1. Run `python scripts/validate_flow_json.py flow.json --strict`.
2. Run `lfx validate flow.json --level 1 --skip-components --skip-edge-types --skip-required-inputs --skip-version-check --skip-credentials`.
3. If installed packages are in scope, run `lfx validate flow.json --level 4 --skip-components --format json`.
4. If the flow should run offline, run `lfx run flow.json "hello" --no-check-variables --format json`.
5. If the flow requires a server, call `/api/v1/run/FLOW_ID_OR_ALIAS` with a small non-secret input and no risky tweaks.
6. Add credentials, global-variable headers, files, and provider network access one dependency at a time.
