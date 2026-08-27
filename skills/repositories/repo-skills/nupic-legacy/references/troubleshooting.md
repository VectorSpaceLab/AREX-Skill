# Root Troubleshooting

Use this root guide before sub-skill debugging when the failure happens before workflow code runs or when the symptom mentions Python version, package imports, compiled bindings, Cap'n Proto, dependency conflicts, or broad runtime setup.

## Cross-cutting failure map

| Symptom | Likely cause | Recovery |
|---|---|---|
| `SyntaxError` at `print ...`, `except ..., e`, or `reader.next()` behavior in an example | Running NuPIC legacy Python 2 code under Python 3 | Use a Python 2.7 environment for NuPIC legacy workflows. Only port syntax if the task is explicitly a migration task. |
| `ImportError: No module named nupic` | Package not installed in the Python interpreter executing the script | Install `nupic` in that interpreter, then run `python scripts/check_nupic_legacy_env.py`. |
| `ImportError: No module named nupic.bindings`, `engine_internal`, `math`, or region internals | Compiled `nupic.bindings` is absent or mismatched | Install a Python-2.7-compatible `nupic.bindings` package. Re-run root smoke, then the relevant sub-skill smoke. |
| `ImportError: No module named capnp` | `pycapnp`/Cap'n Proto missing | Install a Python-2.7-compatible `pycapnp`; prefer a prebuilt package if old Cap'n Proto fails to compile on a modern compiler. |
| `pip check` reports missing `pycapnp` or dependency conflicts | Partial install or mixed modern/legacy dependency set | Repair before workflow verification. NuPIC legacy has old pins; isolate it from modern ML environments. |
| `ValueError` about encoder bits or dimensions | API/config issue after imports pass | Route to `sub-skills/htm-algorithms/references/troubleshooting.md` for direct APIs or `sub-skills/data-and-configuration/` for model params/CSV. |
| OPF result lacks expected prediction keys | Warm-up period, wrong predicted field, or malformed model params | Route to `sub-skills/opf-prediction/references/troubleshooting.md` and check CSV/model params with `sub-skills/data-and-configuration/scripts/validate_nupic_csv.py`. |
| Network `link`/region initialization errors | Region type or input/output endpoint mismatch | Route to `sub-skills/network-api/references/troubleshooting.md` and run `sub-skills/network-api/scripts/network_smoke.py --inspect-region-types`. |
| Swarm `ClientJobs`, MySQL, or worker errors | Service/configuration failure, not necessarily invalid JSON | Route to `sub-skills/swarming/references/troubleshooting.md`; first lint JSON with `sub-skills/swarming/scripts/swarm_config_lint.py`. |

## First command to run

From the root generated skill directory inside the candidate NuPIC environment:

```bash
python scripts/check_nupic_legacy_env.py
```

If it fails only because the interpreter is Python 3 and you are doing a documentation/config-only task, you may run:

```bash
python scripts/check_nupic_legacy_env.py --allow-python3 --skip-api-smoke
```

Do not use that as proof for actual NuPIC workflow execution.

## Sub-skill routing after root triage

- Direct encoders/SP/TM/classifier/anomaly: `sub-skills/htm-algorithms/`.
- CSV streams, model params, config variables, and schema-like validation: `sub-skills/data-and-configuration/`.
- OPF model creation, inference output extraction, checkpoints, and experiment directories: `sub-skills/opf-prediction/`.
- Network API regions, links, custom PyRegion, and region output inspection: `sub-skills/network-api/`.
- Swarm/search definition JSON, `run_swarm` options, generated model params, and MySQL-backed hypersearch: `sub-skills/swarming/`.

## Stop conditions

Stop and ask for environment/service authorization instead of improvising when:

- The task requires installing Python 2.7 or modifying a user-owned environment.
- A full swarming run needs a MySQL service, credentials, or a container.
- The user asks to run long benchmarks, profiling scripts, or full swarming/regression tests.
- The task is actually a Python 3 port or repo maintenance task rather than using NuPIC legacy as a package.
