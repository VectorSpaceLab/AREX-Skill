---
name: serving
description: "Route DeepPavlov REST and socket serving, service settings,
  payload validation, and runtime troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# serving

Use this sub-skill for DeepPavlov service exposure and runtime checks.

## Handle here
- `python -m deeppavlov riseapi ...`
- `python -m deeppavlov risesocket ...`
- `/model`, `/probe`, `/api`, `/docs`, `/metrics`
- `DP_SETTINGS_PATH`, `server_config.json`, `dialog_logger_config.json`
- REST JSON payload keys, batch lengths, and response shape
- Socket framing, payload encoding, and client-side decoding
- HTTPS, host/port, socket type/file, CORS, and Prometheus metrics

## Route elsewhere
- Config selection, training, nested configs, or registries: [pipelines](../pipelines/SKILL.md)
- Text model families and their input/output shapes: [text-models](../text-models/SKILL.md)
- Retrieval, QA, FAQ, ranking, or KBQA model families: [retrieval-qa](../retrieval-qa/SKILL.md)

## Read next
- [API reference](references/api-reference.md)
- [Service configuration](references/service-configuration.md)
- [Troubleshooting](references/troubleshooting.md)
- [Socket payload smoke script](scripts/socket_payload_smoke.py)
