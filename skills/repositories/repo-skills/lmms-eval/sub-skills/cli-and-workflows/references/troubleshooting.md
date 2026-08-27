# cli-and-workflows troubleshooting

Use this page when the user is running or inspecting evals directly from the CLI or Python API.
It focuses on command-line mistakes, cache behavior, reasoning tags, and API entry-point confusion.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unknown task` or `Unknown model` | The registry name is wrong or the user is using a stale alias | Run `lmms-eval tasks list` or `lmms-eval models --aliases` and retry with a canonical name. |
| `--config` run ignores a value | A CLI override wins over YAML, or the YAML key is misspelled | Re-check the merged CLI arguments and fix the config key or override order. |
| Cached outputs look stale | Cache reuse was intentional or the cache key changed unexpectedly | Use `cache_reasoning_smoke.py` to confirm the helper behavior, then refresh or delete cache entries on purpose. |
| `<think>` text is still visible in scoring | Reasoning-tag stripping is disabled, overridden, or configured with the wrong tag pair | Verify `--reasoning_tags` and any task-level override before changing the model output. |
| The Python API call fails but the CLI help works | The code is calling the wrong helper (`simple_evaluate` vs `evaluate`) or passing the wrong task type | Compare the call site against `api-reference.md` and the request-shape table. |
| The no-arg wizard or help command fails on a minimal install | A service extra is missing or the user is invoking a service command from a base-only environment | Switch to the service-ops route and install the needed `server` / `mcp` / `tui` extras. |

## Fast recovery steps

1. Reproduce with `--limit 5` or `--limit 8`.
2. Confirm the model and task names with the bundled registry or CLI smoke.
3. Check whether the run is CLI-first or Python-first.
4. Compare the failure against the API reference before editing code.
5. If the problem is actually about backend selection or task YAML shape, hand it off to the owning sub-skill.
