# Troubleshooting

## Purpose

Read this first for OpenFreeMap import, configuration, deployment, and helper-script failures.

## Fast triage

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `config/.env does not exist` | `ssh_lib` did not find a config file at import time | Create `config/.env` from `config/.env.sample` or set `ENV` to a matching sample name before importing the packages. |
| `config.json` missing or unreadable | The host-side runtime config has not been generated yet | Use the deployment workflow or create a temporary stub only for local inspection. |
| `rclone.conf missing` | Round-robin or bucket-sync workflow was selected without the required bucket credentials | Add the config file before running the HTTP-host or load-balancing workflows. |
| `Please specify DOMAIN_DIRECT or DOMAIN_ROUNDROBIN` | The `.env` file did not define a deployable domain | Fill in the domain values before running deployment. |
| `Please add your email to LETSENCRYPT_EMAIL` | Direct-host TLS was requested without an email address | Add the email or switch to self-signed certs. |
| `needs sudo` | The command is intended for a dedicated Linux host with root access | Re-run on the correct machine or choose the read-only help path. |
| `download-btrfs needs to be run first` | The HTTP host was asked to mount or sync before any btrfs image was downloaded | Run the download step first. |
| `No hosts found on list` | The load balancer has no configured hosts | Fill `HTTP_HOST_LIST` and regenerate config.json. |
| `shrink_btrfs.py` fails immediately | It is a root-only, Btrfs-specific helper | Do not treat it as a general-purpose utility. |

## Import and environment failures

### `ssh_lib` import fails

Checklist:

1. Confirm the repo has a config file at `config/.env` or `config/.env.<ENV>`.
2. Confirm the selected `ENV` value matches an actual file name suffix.
3. Re-run the import from the inspection environment, not the host Python.

### HTTP-host or load-balancer config import fails

Checklist:

1. Confirm a `config.json` exists where the runtime modules expect it.
2. Confirm the JSON contains `domain_direct`, `domain_roundrobin`, `letsencrypt_email`, `skip_planet`, `self_signed_certs`, `http_host_list`, `telegram_token`, and `telegram_chat_id`.
3. Confirm `cloudflare.ini` exists when the round-robin workflow is being inspected.

### `pycurl` problems

If `loadbalancer_lib.shared` fails to import because `pycurl` is missing or incompatible:

- Re-check the editable install.
- Re-run `python -m pip check`.
- Confirm that the inspection environment is using the expected Python version.

## Deployment failures

### SSH / Fabric issues

Common causes:

- wrong host or port
- SSH key not accepted
- `SSH_PASSWD` set incorrectly
- remote user lacks sudo

Recovery:

- verify the target host in `.ssh/config`
- use the deployment workflow with a known-good host
- prefer a clean VM or dedicated server

### Package install on the remote host

If the bootstrap workflow gets stuck on apt, Python, or `pip`:

- the host may not be a clean Ubuntu machine
- the package manager may be waiting for input
- the remote venv may already exist in a half-configured state

Recovery:

- use the quick `SKIP_PLANET=true` path first
- inspect the remote venv and config files before retrying
- avoid running the deployment workflow on a personal dev machine

### TLS and DNS setup

If certbot, Cloudflare, or round-robin DNS steps fail:

- check `LETSENCRYPT_EMAIL`
- check `DOMAIN_DIRECT` versus `DOMAIN_ROUNDROBIN`
- confirm `cloudflare.ini` and `rclone.conf` are present when round-robin publishing is enabled

## HTTP-host failures

- `mount` complains that the btrfs image does not exist: run the download step first.
- `nginx-config` fails: confirm the mount directory and config JSON exist.
- `sync` is a no-op: check whether the remote version and asset files changed.
- A style URL works in the app but not on the host: confirm the generated nginx config contains the expected style alias and path.

## Tile-generation failures

- `make-tiles` is slow or memory-heavy: this is expected for Planetiler and the full planet path.
- `upload-area` fails because multiple runs exist: clean the area so exactly one run remains.
- `set-version` says the version is not available: the bucket may not have the run yet.
- `shrink_btrfs.py` errors on resize: it is a Btrfs-specific loop-mount helper and should only be used on the image it created.

## Benchmark helper failures

- `nginx_to_path_list.py` writes an empty file: the access sample likely had no 200 GET PBF rows.
- `wrk_custom_list.lua` replays the wrong path prefix: fix the path-list file or the helper's base path setting.
- benchmark numbers look much lower over the internet than in the docs: rerun on localhost.

## When to stop and ask for more input

Stop and ask when the failure needs one of these:

- actual SSH credentials or sudo access
- a real domain or Cloudflare account
- real bucket credentials
- a dedicated server, Btrfs image, or large planet download
- a fresh deployment config that the repo does not ship by default

## Escalation map

- Bootstrap / host provisioning problems → `sub-skills/deployment/`
- HTTP-host runtime problems → `sub-skills/http-host/`
- Tile generation / upload problems → `sub-skills/tile-generation/`
- DNS / round-robin / cert publishing problems → `sub-skills/load-balancing/`
- Public-style integration or client code issues → `references/client-integration.md`
- Benchmark helper issues → `references/benchmarking.md`
