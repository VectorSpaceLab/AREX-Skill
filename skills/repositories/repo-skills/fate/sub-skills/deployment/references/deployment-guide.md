# Deployment guide

This guide summarizes the documented FATE deployment paths and the safe checks that usually follow them.
It is intentionally copyable and avoids host mutation beyond the commands already documented by the project.

## How the stack fits together

- `pyfate==2.2.0` gives you the importable `fate` package for local module work.
- `fate_client[fate,fate_flow]==2.2.0` adds the service-backed client and the `fate_flow` service tooling.
- `fate_flow init` binds the service home and ports.
- `fate_flow start` and `fate_flow status` manage the service lifecycle.
- `pipeline init` points the client at the running Fate-Flow endpoint.
- `python -m fate.components` exposes the component catalog and task schema; see `../component-runtime/SKILL.md` for details.
- `flow test toy` is the documented first smoke check after a service-backed install.

## Choose a path

- **PyPI only**: install `pyfate` when you only need local modules or launcher-style runs.
- **PyPI + Fate-Flow**: install `fate_client[fate,fate_flow]` when you want service-backed jobs.
- **Standalone Docker**: use the single-node Docker image for a quick local service stack.
- **Host package**: use the precompiled tarball when you want a host-installed stack.
- **Docker Compose / all-in-one**: use the documented multi-host bundle when you need a containerized cluster layout.

## Command matrix

| Path | Copyable bootstrap | Start / deploy | Safe follow-up |
| --- | --- | --- | --- |
| PyPI only | `pip install pyfate==2.2.0` | No service starts here | `python -m fate.components --help`; then hand off to `../local-launchers/SKILL.md` |
| PyPI + Fate-Flow | `pip install fate_client[fate,fate_flow]==2.2.0` | `fate_flow init --ip 127.0.0.1 --port 9380 --home "$HOME_DIR"`<br>`pipeline init --ip 127.0.0.1 --port 9380`<br>`fate_flow start` | `fate_flow status`; `pipeline show`; `pipeline site-info`; then run the toy smoke that matches your install guide |
| Standalone Docker | `export version=2.2.0`<br>`docker pull federatedai/standalone_fate:${version}`<br>or<br>`wget https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/fate/${version}/release/standalone_fate_docker_image_${version}_release.tar.gz`<br>`docker load -i standalone_fate_docker_image_${version}_release.tar.gz` | `docker run -it --name standalone_fate -p 8080:8080 federatedai/standalone_fate:${version}` | Inside the container shell: `source /data/projects/fate/bin/init_env.sh` and then run the single-node toy smoke from the docs |
| Host package | `wget https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/fate/${version}/release/standalone_fate_install_${version}_release.tar.gz`<br>`tar -xzvf standalone_fate_install_${version}_release.tar.gz` | `cd standalone_fate_install_${version}_release`<br>`bash bin/init.sh init`<br>`bash bin/init.sh status`<br>`bash bin/init.sh start`<br>`source bin/init_env.sh` | `flow test toy -gid 10000 -hid 10000` |
| Docker Compose / all-in-one | Documented bundle flow only: `bash ./generate_config.sh` then `bash ./docker_deploy.sh all` or `bash ./docker_deploy.sh 10000` | Requires Docker, Docker Compose, SSH keyless access, and free service ports on the target hosts | `docker-compose ps` on a deployed bundle; then `docker-compose exec fateflow bash` and run the multi-party toy smoke from the compose/all-in-one guide |

## Toy smoke variants in the docs

- Single-node / host-package / standalone Docker: `flow test toy -gid 10000 -hid 10000`
- Docker Compose / all-in-one: `flow test toy --guest-party-id 10000 --host-party-id 9999` (use the party IDs from your bundle)

## Port map from the deployment guides

- `8080` — Fateboard
- `9360` — Fate-Flow gRPC
- `9380` — Fate-Flow HTTP
- `9370` — OSX
- `4670` — Eggroll clustermanager
- `4671` — Eggroll nodemanager

## Practical startup order for service-backed installs

1. Initialize the service configuration.
2. Start the service layer.
3. Confirm the process and port are up.
4. Run the toy smoke check.
5. Move on to pipeline recipes in `../pipeline-workflows/SKILL.md`.

## What not to do by default

- Do not run remote deployment fanout or teardown from this skill.
- Do not treat `bin/service.sh`, `bin/install_os_dependencies.sh`, `bin/init_env.sh`, or the docker-deploy scripts as portable runtime entrypoints.
- Do not use this skill for service-free local algorithm execution; use `../local-launchers/SKILL.md`.
