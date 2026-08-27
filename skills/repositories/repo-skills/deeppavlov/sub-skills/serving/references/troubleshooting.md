# Troubleshooting

Use this checklist when serving fails or the client cannot talk to the service.

## Fast workflow

1. Inspect the active settings path with `python -m deeppavlov.settings`.
2. Call `GET /api` to confirm argument names and output names.
3. Call `POST /probe` with the same batch shape you plan to use for `/model`.
4. Call `POST /model` only after the probe succeeds.
5. Watch `/metrics` if you need request counters or latency.

## Common REST failures

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| HTTP 400 `got empty request` | All request values were missing or empty | Send at least one non-empty list. |
| HTTP 400 `got empty array as model argument` | A named field was sent as `[]` | Fill every batch list with at least one item. |
| HTTP 400 `got several different batch sizes` | Batch lists have different lengths | Make all request lists the same length. |
| Unexpected output layout | `COMPATIBILITY_MODE` changed the response format | Unset the variable for modern clients or keep it only for legacy compatibility. |
| HTTP 404 on `/model` | A custom `model_endpoint` changed the path | Read the active server settings and use the reported endpoint. |
| TLS start failure | Missing or unreadable key/cert files | Pass `--key` and `--cert`, or fix the paths in the settings file. |

## Common socket failures

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Client cannot connect | TCP/UNIX mismatch or wrong host/port/file | Match `--socket-type` and `--socket-file` to the server. |
| JSON decode error from the socket body | Wrong frame length or body bytes | Use the 4-byte little-endian header and `encode(...)` to build requests. |
| `nonempty array expected but got ...` | A socket payload key was present with `[]` | Send a non-empty list for that argument. |
| `got empty request` | All values were omitted or null | Include at least one populated batch field. |

## Logging and observability

- Dialog logs are off by default; enable them in `dialog_logger_config.json`.
- The log root and logger name determine where request/response logs are written.
- `/metrics` is the right place to confirm live request traffic, request counts, and latency.

## When the problem is upstream of serving

If the model cannot be built, imported, or downloaded, the failure is usually in the config or model-family workflow rather than in the service layer. Hand that case back to the model/config sub-skill instead of debugging the API transport first.
