# Serving troubleshooting

| Symptom | Cause | Recovery |
|---|---|---|
| CLI rejects config | Missing `--config`, flat file, or invalid nested fields | Provide `generator.model_path`; use `server`, `default_request`, and optional `streaming` mappings; validate before launch. |
| HTTP returns 400 | Invalid size, type, request field, input reference, or unsupported preset override | Read the error path, use `WIDTHxHEIGHT`, keep init-only fields in generator config, and test a minimal typed request. |
| HTTP returns 503 | Generator not loaded or shutdown underway | Check model access, startup logs, backend, and health; do not retry indefinitely while initialization is failing. |
| HTTP defaults override client unexpectedly | Operator wrote fields in `default_request` or merge intent was misunderstood | Remove unintended explicit defaults; preserve only fields the operator intends to pin. |
| WebSocket immediately closes | Opening frame was not `session_init_v2`, or initialization validation failed | Send the required frame first and validate preset, stream mode, inputs, and optional state. |
| No binary media arrives | `media_init` not emitted, wrong stream mode, or generation failed | Consume JSON error/status frames first; ensure client handles fMP4 and waits for media initialization. |
| Session times out or caps early | Idle timeout or segment cap | Increase the appropriate streaming config value only within resource limits; start a new session after a terminal state. |
| Prompt enhancement/safety fails | Optional provider, key, classifier, or network absent | Disable the feature for a baseline server or install/configure the exact optional dependency and credential separately. |
| Port bind or output errors | Port in use, permissions, or output path invalid | Choose a free port and writable output directory; avoid running a public listener without deployment controls. |
