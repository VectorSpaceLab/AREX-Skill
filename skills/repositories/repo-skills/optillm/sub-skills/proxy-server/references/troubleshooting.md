# Proxy Server Troubleshooting

## `401 Invalid Authorization header`

**Cause:** `--optillm-api-key` is configured and the client did not send `Authorization: Bearer <key>`.

**Fix:** Set the OpenAI SDK `api_key` to the server key or add the bearer header. `/health` bypasses auth, so a healthy `/health` response does not prove chat calls are authorized.

## Server tries local model loading unexpectedly

**Cause:** `OPTILLM_API_KEY` is set. In OptiLLM, that environment variable activates built-in local inference.

**Fix:** Unset `OPTILLM_API_KEY` for external provider proxying. Use `OPENAI_API_KEY`, `CEREBRAS_API_KEY`, or `AZURE_*` for upstream credentials. If you need server auth too, set `--optillm-api-key` deliberately and test the client bearer token.

## SSL/certificate errors

**Symptoms:** upstream provider calls fail on certificate verify errors.

**Fix:** Prefer `--ssl-cert-path` / `OPTILLM_SSL_CERT_PATH` with a CA bundle. Use `--no-ssl-verify` / `OPTILLM_SSL_VERIFY=false` only for controlled development debugging because it disables TLS verification.

## `none` cannot be combined

**Symptom:** error says `'none' approach cannot be combined with other approaches`.

**Fix:** Use `none-model` or the raw model for direct proxying. Do not use `none&moa-model` or `none|moa-model`.

## Unknown approach or wrong model split

**Cause:** parser consumes leading dash-separated segments only while they are known approaches/plugins, `&`, or `|` groups. A typo becomes part of the model or an unknown approach.

**Fix:** Inspect offline with:

```bash
python ../../optimization-approaches/scripts/approach_matrix.py --parse 'bon|moa|mcts-gpt-4o-mini'
```

Run from this reference directory with the path above, or use the absolute path to the bundled helper inside the generated skill tree.

## Provider does not support multiple completions

**Symptoms:** `n`, BoN, MoA, or self-consistency fails or returns one response.

**Fix:** Pick approaches that work with sequential single calls or model-native responses: `cot_reflection`, `leap`, `plansearch`, `rstar`, `rto`, `self_consistency`, `re2`, or `z3` depending on task. When using the built-in local inference server, multiple responses are better supported, but model loading requirements apply.

## Streaming surprises

OptiLLM applies approaches first, then streams the final response(s) as SSE chunks. This is not necessarily token-by-token upstream streaming. For exact upstream streaming behavior, use `none` direct proxy and test the provider path.

## Batch mode rejects requests

**Causes:** streaming enabled, model mismatch, different approach operation, or incompatible request shape.

**Fix:** Turn off streaming, group requests by model and approach, or disable batch mode. Batch mode is intentionally fail-fast rather than silently falling back.

## Server reachable but `/v1/models` fails

`/v1/models` may call the upstream provider when `base_url` is configured. If the provider model endpoint is unavailable, `/health` can still pass while `/v1/models` fails. Check provider credentials, base URL, and network route.

## Public binding risk

Default host is `127.0.0.1`. Before using `--host 0.0.0.0`, require a deliberate network/security plan: server auth, firewall/reverse proxy, TLS termination, and logging policy.
