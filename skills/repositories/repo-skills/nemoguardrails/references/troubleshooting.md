# Cross-Cutting Troubleshooting

Use this reference when the failure does not yet belong clearly to installation, config, runtime, evaluation, or source-checkout work.

## First split the problem

| Symptom | Route |
| --- | --- |
| Package will not install, import, or expose the CLI | `../sub-skills/setup-and-basics/SKILL.md` |
| YAML, Colang, prompts, catalog rails, actions, or provider registration fail while loading a config | `../sub-skills/configure-rails/SKILL.md` |
| `generate`, `check`, streaming, CLI chat, server endpoints, HTTP schemas, state/thread handling, or LangChain wrapping fail | `../sub-skills/run-rails/SKILL.md` |
| Evaluation output, compliance checks, logging, tracing, metrics, telemetry, or privacy controls are confusing | `../sub-skills/evaluate-and-observe/SKILL.md` |
| The task requires editing the repository, adding providers, changing docs/tests, or preparing issue/PR text | `../sub-skills/repo-development/SKILL.md` |

## Safe triage order

1. Confirm Python is `>=3.10,<3.14` and the package imports.
2. Run install-only checks before runtime checks:
   - `python -m pip check`
   - `python -m nemoguardrails --help`
   - `python sub-skills/setup-and-basics/scripts/check_install.py`
3. Validate the config without generation:
   - `python sub-skills/configure-rails/scripts/validate_config.py --config path/to/config`
4. Use deterministic runtime smokes before any live provider:
   - `python sub-skills/run-rails/scripts/deterministic_chat_smoke.py`
   - `python sub-skills/run-rails/scripts/server_schema_smoke.py`
5. Only after the local package, config, and deterministic runtime checks pass should you attempt live model providers, external telemetry, cloud moderation APIs, Docker, or heavyweight notebook workflows.

## Common root causes

| Problem | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` mentions a missing optional dependency | The selected workflow needs an extra such as `server`, `eval`, `tracing`, `chat-ui`, `sdd`, `jailbreak`, `multilingual`, or `gcp`. | Install the smallest related extra and rerun the bundled install checker. |
| Console command is unavailable but imports work | Entry points were not generated or the environment path is not active. | Try `python -m nemoguardrails --help`; reinstall the package in the active environment if module invocation works. |
| A no-provider smoke tries to download embedding assets | A default embedding search provider was used instead of a deterministic or mocked provider. | Use the bundled deterministic chat smoke or replicate its local embedding patch. |
| Config loads but runtime generation reaches a live provider unexpectedly | The config declares a real model/provider and the call path performs generation. | Use `validate_config.py` for config-only checks or provide a fake/mock LLM for local runtime smokes. |
| Server health succeeds but chat requests fail | `/v1/health` is shallow and does not prove upstream model credentials, config validity, or generation paths. | Validate the config, run the server schema smoke, then inspect provider configuration and request shape. |
| Evaluation wants to call an LLM judge | Many eval workflows require a configured model or judge. | Decide whether the task is an offline data/schema check or a live evaluation; do not run live eval without explicit credentials and scope. |
| Unit tests or examples try to contact live providers | The wrong command or selector was used for source-checkout validation. | Use checkout-scoped `make test` wrappers and fake-model tests; route source-edit validation to `repo-development`. |

## Privacy and self-containment rules

- Do not paste local virtualenv paths, private package install locations, credentials, API keys, telemetry staging URLs, or source-checkout-only artifact paths into user-facing runtime answers.
- Do not tell future users to open the original source docs/examples/tests to use this skill. Distill the needed fact into the relevant sub-skill reference or use a bundled helper script.
- Treat live providers, telemetry staging, cloud moderation, Docker deployments, notebooks, and benchmarks as explicit opt-in workflows with their own prerequisites.
