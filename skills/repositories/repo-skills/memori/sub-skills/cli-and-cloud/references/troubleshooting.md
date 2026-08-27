# CLI and Cloud Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing API key | `MEMORI_API_KEY` is unset or the request is being run in cloud mode unexpectedly | set the key or switch to BYODB with `conn=...` |
| Quota or authorization error | the cloud request is valid but the account or token cannot continue | check quota, sign-in status, and request shape |
| `422` validation failure | a required field or identifier is malformed | fix the payload before retrying |
| `433` / SSL / proxy rejection | the service or proxy rejected the HTTPS path | verify CA/proxy settings and the base URL |
| Timeout or connection error | transient network failure or too-short timeout | retry after checking the network path |
| `session_id` without `project_id` | invalid agent-filter combination | always supply `project_id` when filtering by `session_id` |
| Nothing appears to persist | attribution was not set or the script exited before the background write finished | set attribution and wait for augmentation when needed |
| Dangerous cluster delete command | a destructive maintenance command was treated as a user-facing workflow | never suggest it as a default action |

## Recovery order

1. Confirm whether the task is cloud or BYODB.
2. Check API key, entity, project, and session identifiers.
3. Separate payload validation errors from authorization or transport errors.
4. Use the bundled CLI smoke before assuming the install itself is broken.

## Avoid

- Do not suggest credential leakage or hard-coded private keys.
- Do not suggest destructive cluster commands as a routine fix.
- Do not move the user to storage or LLM troubleshooting unless the symptom
  actually belongs there.
