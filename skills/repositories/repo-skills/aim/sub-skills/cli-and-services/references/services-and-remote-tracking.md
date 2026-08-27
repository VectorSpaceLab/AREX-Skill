# Aim services, remote tracking, notebook UI, and deployment concepts

Aim has two service commands that are easy to confuse:

| Need | Command | Default address | Client/user connects with |
| --- | --- | --- | --- |
| Browse and compare runs in a web UI | `aim up` | `127.0.0.1:43800` | Browser URL such as `http://127.0.0.1:43800` |
| Send SDK tracking data from another process or host | `aim server` | `0.0.0.0:53800` | Python SDK repository URL such as `aim://host:53800` |

A production-like setup often runs both commands against the same repository directory: `aim server` accepts writes from training jobs, while `aim up` serves the UI for humans.

## Choosing `aim up` vs `aim server`

Use `aim up` when the task is to:

- open the Aim UI locally;
- expose the UI behind a browser reverse proxy;
- browse an existing repo in read-only mode;
- embed the UI in a notebook.

Use `aim server` when the task is to:

- let training jobs on other machines create `Run(repo='aim://...')`;
- centralize tracking data from multiple clients;
- receive writes over HTTP/WebSocket transport.

Do not tell users that `aim up` is the remote tracking endpoint. It is the UI service. Do not tell users that `aim server` is the full browser UI. Run UI separately if needed.

## Local UI launch pattern

Minimal safe setup:

```bash
mkdir -p <repo_dir>
aim init --repo <repo_dir> --skip-if-exists
aim up --repo <repo_dir> --host 127.0.0.1 --port 43800 --log-level warning
```

Operational notes:

- `aim up` is long-running and exits with Ctrl+C.
- `--port 0` requests an available port.
- `--read-only` is the CLI-supported read-only UI mode. It is useful for shared browsing where users should not mutate data through the UI.
- `--base-path <path>` mounts the UI under a path prefix. Aim normalizes `ui` to `/ui` and trims a trailing slash.
- `--ssl-keyfile` and `--ssl-certfile` enable HTTPS directly in the Uvicorn process.
- `--uds <socket_file>` can be used when a local reverse proxy speaks to Uvicorn over a Unix socket.
- `--profiler` writes profiling data into the Aim repository; enable only for diagnosis.
- `--dev` is for package development, not normal operation.

For external users, prefer a reverse proxy or SSH tunnel over binding the UI directly to a public interface. If `--host 0.0.0.0` is required, confirm firewall, authentication proxy, and TLS expectations first.

## Remote tracking server pattern

Server-side setup:

```bash
mkdir -p <repo_dir>
aim init --repo <repo_dir> --skip-if-exists
aim server --repo <repo_dir> --host 0.0.0.0 --port 53800 --log-level warning
```

Client-side SDK pattern:

```python
from aim import Run

run = Run(repo='aim://tracking.example.com:53800')
run['hparams'] = {'learning_rate': 0.001, 'batch_size': 32}
run.track(0.42, name='loss', step=1, context={'subset': 'train'})
run.finalize()
```

Remote tracking uses HTTP and WebSocket endpoints internally. The client probes HTTP and HTTPS support, checks server/client version compatibility, and uses an internal queue for remote write instructions.

### Remote server behind a reverse proxy or base path

When the tracking API is mounted under a path prefix, set the server base path and include the same path in the client `aim://` URL:

```bash
aim server --repo <repo_dir> --host 127.0.0.1 --port 53800 --base-path /aim-api
```

```python
from aim import Run
run = Run(repo='aim://tracking.example.com:53800/aim-api')
```

The reverse proxy must forward both HTTP requests and WebSocket upgrade traffic for the mounted path. If the UI is also proxied, configure `aim up --base-path <ui_path>` separately; the UI and tracking API path prefixes do not have to match.

### TLS and certificates

For direct TLS termination in Aim services, use:

```bash
aim server --repo <repo_dir> --ssl-keyfile <server.key> --ssl-certfile <server.crt>
aim up --repo <repo_dir> --ssl-keyfile <server.key> --ssl-certfile <server.crt>
```

For self-signed or private certificates, configure clients with the certificate bundle expected by the Aim client via the `__AIM_CLIENT_SSL_CERTIFICATES_FILE__` environment variable. Treat certificate bundles and private keys as secrets when they contain key material; do not commit them or paste their contents into logs.

### Access control boundary

The inspected service commands expose host/port, TLS, base-path, and log-level controls, but the CLI evidence does not provide an application-level authentication setup recipe. For multi-user or public deployments, put Aim behind a trusted network boundary, VPN, SSH tunnel, or authentication-capable reverse proxy.

## Running both UI and remote tracking

Use separate processes, usually on separate ports:

```bash
# Process 1: remote tracking API for SDK writes
aim server --repo <repo_dir> --host 0.0.0.0 --port 53800 --log-level warning

# Process 2: browser UI for humans
aim up --repo <repo_dir> --host 127.0.0.1 --port 43800 --read-only --log-level warning
```

If both are behind a reverse proxy:

- `/aim/` can route to `aim up --base-path /aim`.
- `/aim-api/` can route to `aim server --base-path /aim-api`.
- Client SDK URLs should use `aim://<host>/aim-api` with the actual host/port combination exposed by the proxy.

## Notebook UI

Inside IPython/Jupyter notebooks:

```jupyter
%load_ext aim
%aim up
```

The notebook magic supports `up` and `version`. Source inspection shows the magic parser accepts `--port=<value>`, `--host=<value>`, `--repo=<value>`, and `--proxy-url=<value>` forms. The notebook `up` command defaults to a notebook-specific base path and port so the UI can be embedded in an iframe.

Example with an explicit repo and port:

```jupyter
%load_ext aim
%aim up --repo=./my-aim-repo --host=127.0.0.1 --port=43801
```

In managed notebook platforms that require a proxy URL, pass `--proxy-url=<external_proxy_url>` and verify that the proxy forwards the selected port and path. Do not run notebook UI commands from non-notebook automation; use the CLI service commands instead.

## Docker deployment concept

Aim publishes container images whose default command is the UI command. A conceptual container deployment maps the UI port `43800` for `aim up` or the tracking port `53800` for `aim server`, and mounts a persistent volume for the repository directory.

Safe Docker guidance:

- Pin an image tag instead of relying on a moving latest tag.
- Mount persistent storage for the `.aim` repository; otherwise runs may disappear when the container is removed.
- Map only the required port and put public services behind TLS/authentication boundaries.
- Do not copy or run maintainer Docker build scripts as user deployment scripts.
- Treat Docker as a deployment choice requiring user confirmation about ports, volumes, and credentials.

## Environment-specific lifecycle scripts

Aim has deployment-oriented service-script concepts for managed notebook environments. Treat these as reference patterns only: inspect the target platform's lifecycle-hook semantics, environment variables, proxy paths, and persistence model before adapting. Do not run environment-specific startup scripts blindly on a workstation or CI host.
