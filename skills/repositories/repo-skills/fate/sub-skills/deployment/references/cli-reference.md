# CLI reference

This reference focuses on the service-backed command surface that matters during deployment.
It intentionally stays narrow so the later recipe and component sub-skills can own the heavier task-specific details.

## Command groups

| Command | What it is for | Notes |
| --- | --- | --- |
| `fate_flow --help` | Service lifecycle entrypoint | Verified commands: `init`, `restart`, `start`, `status`, `stop`, `version`. |
| `fate_flow init --ip <ip> --port <port> --home <path>` | Initialize the Fate-Flow service home and listen address | The installed help exposes `--ip`, `--port`, and `--home`. |
| `fate_flow start` / `fate_flow status` | Start the service and confirm it is running | Use `status` before running any service-backed smoke check. |
| `pipeline --help` | Client-side setup and inspection entrypoint | Verified commands: `init`, `show`, `site-info`. |
| `pipeline init --ip <ip> --port <port> [--path <path>]` | Point the client at the Fate-Flow service | The installed help exposes `--path` in addition to `--ip` and `--port`. |
| `python -m fate.components --help` | Component catalog and task-schema CLI | The package exposes `component` and `test` groups, and component commands are hyphenated. See `../component-runtime/SKILL.md`. |
| `python -m fate.components component list` | List built-in components | Safe post-install smoke check. |
| `python -m fate.components component task-schema` | Generate task schema metadata | Use the hyphenated command name, not `task_schema`. |
| `flow test toy ...` | End-to-end service smoke | Run only after the service and ports are ready. |

## How the pieces fit together

- `pyfate` provides the importable `fate` package for local module work.
- `fate_flow` manages the service side of a deployment.
- `pipeline` binds the client side to that service.
- `python -m fate.components` inspects component metadata and task schemas.
- `flow test toy` proves the service path end to end before you move on to training or prediction recipes.

## Safe deployment order

1. Check the environment with `scripts/deployment_preflight.py`.
2. Run `fate_flow init` for the chosen path.
3. Run `pipeline init` if you are using the service-backed client.
4. Start the service with `fate_flow start`.
5. Confirm health with `fate_flow status`.
6. Run the documented toy smoke check.
7. Hand off to `../pipeline-workflows/SKILL.md` for train/predict recipes.

## Reference-only wrappers from the repo

The docs mention host-specific wrappers such as:

- `bin/service.sh`
- `bin/init_env.sh`
- `bin/install_os_dependencies.sh`
- `deploy/docker-compose/docker-deploy/docker_deploy.sh`
- `deploy/docker-compose/docker-deploy/generate_config.sh`

Use them as evidence for service layout and deployment flow, not as portable runtime entrypoints in this skill.
