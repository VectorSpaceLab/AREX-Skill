# Deployment API reference

## Purpose

Read this when you need the command families and helper signatures behind the clean-server bootstrap workflow.

## Entry-point summary

`init-server.py` is the top-level deployment CLI. It exposes these commands:

- `http-host-static`
- `http-host-autoupdate`
- `tile-gen`
- `roundrobin-dns-writer`
- `loadbalancer`
- `http-host-sync`
- `debug`

Each command accepts a hostname plus optional `--user`, `--port`, and `--noninteractive` flags. `tile-gen` also accepts `--cron` and `--reinstall`.

## Helper signatures verified from source

| Helper | Signature | Role |
| --- | --- | --- |
| `get_connection` | `(hostname, user, port)` | Builds a Fabric connection using `SSH_PASSWD` when present. |
| `common_options` | `(func)` | Adds common hostname / user / port / confirmation options. |
| `prepare_shared` | `(c)` | Creates the `ofm` user, installs base packages, uploads config, and prepares the shared venv. |
| `prepare_venv` | `(c)` | Uploads and runs the remote venv bootstrap script. |
| `prepare_http_host` | `(c)` | Installs nginx, certbot, and the HTTP-host runtime files. |
| `run_http_host_sync` | `(c)` | Runs the remote HTTP-host sync command. |
| `prepare_tile_gen` | `(c, *, enable_cron)` | Installs Planetiler, uploads tile-generation files, and optionally installs the cron job. |
| `upload_http_host_files` | `(c)` | Uploads the HTTP-host package tree to the remote host. |
| `upload_config_json` | `(c)` | Builds the runtime JSON config from the `.env` values. |
| `setup_roundrobin_writer` | `(c)` | Installs the round-robin certificate publish hook and requests the Cloudflare cert. |
| `setup_loadbalancer` | `(c)` | Installs the load-balancer package and cron job. |

## Installation facts relevant to deployment

The deployment workflow depends on:

- `click`
- `fabric`
- `requests`
- `python-dotenv`
- `pycurl` for the runtime helper modules
- `rclone`, `nginx`, `certbot`, `java`, `btrfs-progs`, and other host tools on the remote machine

## How the commands are meant to be used

- `http-host-static` is the quick first pass for a direct HTTP host.
- `http-host-autoupdate` adds the cron file for ongoing sync.
- `tile-gen` prepares the tile-generation server; `--cron` installs the cron file.
- `roundrobin-dns-writer` is the one-time certificate publish path for a round-robin domain.
- `loadbalancer` installs the DNS health-checker and cron entry.
- `http_host_sync` runs the sync step without the broader bootstrap.
- `debug` skips the confirmation prompt and runs the sync command path directly.

## Read this before editing or extending deployment guidance

If a future question asks how the host bootstrap is structured, start here and then consult the workflow and troubleshooting notes. The source CLI remains the authoritative implementation, but this reference is the durable summary future agents should use first.
