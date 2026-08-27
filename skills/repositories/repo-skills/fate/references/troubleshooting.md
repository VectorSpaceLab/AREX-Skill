# FATE root troubleshooting

Use this file for cross-cutting failures that appear before a workflow has a clear owner. After the first triage step, route to the nearest sub-skill troubleshooting reference.

## Fast triage matrix

| Symptom | First checks | Route next |
| --- | --- | --- |
| `ModuleNotFoundError: fate` or `python -m fate.components` cannot import | Run `python scripts/check_fate_install.py`; install/repair `pyfate==2.2.0`; confirm `import fate` works. | `sub-skills/component-runtime/references/troubleshooting.md` for component CLI, or `sub-skills/local-launchers/references/troubleshooting.md` for local APIs. |
| `ModuleNotFoundError: fate_utils` | Install/repair `fate_utils==0.1.0` or reinstall the FATE package set. If building from source, make sure the Rust-backed wheel can be resolved for the target Python/platform. | `references/package-overview.md` for package surfaces. |
| `No module named pkg_resources` during component discovery/listing | Install or pin a `setuptools` build that provides `pkg_resources`; construction was verified with `setuptools==80.9.0`. | `sub-skills/component-runtime/references/troubleshooting.md`. |
| `python -m fate.components component task_schema` fails | Use the hyphenated command: `python -m fate.components component task-schema`. | `sub-skills/component-runtime/SKILL.md`. |
| `fate_flow` or `pipeline` command is missing | Use `python scripts/check_fate_install.py --include-service`; install the service/client packages for FateFlow-backed work. | `sub-skills/deployment/SKILL.md`. |
| FateFlow connection refused, endpoint unreachable, or `pipeline site-info` fails | Confirm the service is initialized/running, the client was initialized with the right `--ip`/`--port`, and no required port is already occupied. | `sub-skills/deployment/references/troubleshooting.md`. |
| Docker/Compose permission, image, port, SSH, or cluster rollout errors | Do not run destructive deployment scripts blindly. Use the deployment preflight helper and inspect service/port/SSH prerequisites first. | `sub-skills/deployment/SKILL.md`. |
| Upload YAML has missing fields, wrong table names, bad partition count, or unclear roles | Run `python sub-skills/pipeline-workflows/scripts/validate_upload_config.py <config> [--check-files]`. | `sub-skills/pipeline-workflows/references/troubleshooting.md`. |
| Pipeline task cannot find a table or role mapping is wrong | Recheck `namespace`, `table_name`, guest/host/arbiter party ids, and `Reader` host index mapping. | `sub-skills/pipeline-workflows/SKILL.md`. |
| Local launcher hangs, spawns unexpected processes, or rejects party strings | Verify this is meant to be service-free, use tiny data first, and check party strings such as `guest:9999` and `host:10000`. | `sub-skills/local-launchers/references/troubleshooting.md`. |
| GPU, DeepSpeed, Spark, Eggroll, RabbitMQ, or Pulsar errors | Treat these as optional or service-backed backends unless the user asked for them and the environment is explicitly verified. Do not use CPU import success as proof of GPU/cluster capability. | `sub-skills/deployment/` for services; `sub-skills/local-launchers/` for local CPU substitutes. |
| A doc/example path from the original checkout is missing | Use bundled skill references/scripts instead of source-checkout paths. If the task depends on changed upstream behavior, compare with `references/repo-provenance.md`. | Root skill staleness check. |

## Recommended safe checks

```bash
python scripts/check_fate_install.py
python scripts/check_fate_install.py --include-service
python sub-skills/component-runtime/scripts/check_component_cli.py
python sub-skills/local-launchers/scripts/check_launcher_imports.py --check-standard
python sub-skills/pipeline-workflows/scripts/validate_upload_config.py <upload-config.yaml>
python sub-skills/deployment/scripts/deployment_preflight.py --mode all
```

All commands above are intended as safe checks. They do not start training, upload data, start services, or mutate the host unless a sub-skill documents an explicit heavy or service action and the user asks for it.

## Routing reminders

- If the user needs a FateFlow-backed job, route to `pipeline-workflows` after deployment/client prerequisites are satisfied.
- If the user says no service, local simulation, direct module API, or `launch(run_fn)`, route to `local-launchers`.
- If the user asks whether a component name, role, stage, artifact, or task config is valid, route to `component-runtime`.
- If the user asks how to install/start/check services, route to `deployment`.
