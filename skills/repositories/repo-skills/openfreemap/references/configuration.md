# Configuration

## Purpose

Read this when a task mentions `.env`, `config.json`, bucket credentials, SSH passwords, or the deployment prerequisites for OpenFreeMap.

## Where configuration lives

OpenFreeMap uses two layers of configuration:

1. `config/.env` or `config/.env.<ENV>` for bootstrap and deploy-time variables.
2. A generated `config.json` on the server side for runtime modules such as `http_host`, `tile_gen`, and `loadbalancer`.

The deployment workflow creates the JSON config from the `.env` values.

## `.env` / `.env.sample` variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `SSH_PASSWD` | `init-server.py` / `ssh_lib` | Optional SSH password for Fabric connections. Leave empty when SSH keys are used. |
| `DOMAIN_DIRECT` | deployment + HTTP-host | Primary domain/subdomain for the direct host. |
| `LETSENCRYPT_EMAIL` | deployment + certbot | Email used for Let's Encrypt certificates. Required when `DOMAIN_DIRECT` is set and self-signed certs are not enabled. |
| `SKIP_PLANET` | deployment + HTTP-host sync | When `true`, skip the full planet download for a faster first-pass deployment. |
| `SELF_SIGNED_CERTS` | deployment + HTTP-host nginx | When `true`, stop after generating self-signed certs instead of requesting Let's Encrypt certs. |
| `DOMAIN_ROUNDROBIN` | deployment + load balancing | Alternate round-robin domain used for multi-host certificate distribution and DNS updates. |
| `HTTP_HOST_LIST` | load balancing | Comma-separated list of HTTP-host IPs checked by the load balancer. |
| `TELEGRAM_TOKEN` | load balancing | Telegram bot token for status alerts. |
| `TELEGRAM_CHAT_ID` | load balancing | Telegram chat id for load-balancer alerts. |

## Generated `config.json` fields

The runtime packages read a JSON object with these fields:

| Field | Used by | Meaning |
| --- | --- | --- |
| `domain_direct` | `http_host_lib` | Direct-host domain, if any. |
| `domain_roundrobin` | `http_host_lib`, `loadbalancer_lib` | Round-robin domain, if any. |
| `letsencrypt_email` | `http_host_lib` | Email used for certificate requests. |
| `skip_planet` | `http_host_lib` | Whether HTTP-host sync should skip the planet download path. |
| `self_signed_certs` | `http_host_lib` | Whether nginx should stop at self-signed certs. |
| `http_host_list` | `loadbalancer_lib` | List of HTTP-host IPs to probe. |
| `telegram_token` | `loadbalancer_lib` | Telegram token used for alerts. |
| `telegram_chat_id` | `loadbalancer_lib` | Telegram chat id used for alerts. |

## Related files and directories

- `config/.env.sample` — starting point for bootstrap values.
- `config/cloudflare.ini.sample` — DNS challenge credentials for round-robin certificate setup.
- `config/rclone.conf.sample` — rclone remote definition for bucket uploads.
- `/data/ofm/config/config.json` on deployed hosts — generated runtime config.
- `/data/ofm/config/deployed_versions/` on deployed hosts — current published version markers.

## Common configuration facts

- `ssh_lib` reads `config/.env` by default, or `config/.env.<ENV>` when `ENV` is set.
- The host-side modules fall back to `repo_root/config` only when `/data/ofm` is absent.
- The deployment workflow assumes a clean server and writes into `/data/ofm`, `/data/nginx`, and `/mnt/ofm`.
- Round-robin setup requires both `cloudflare.ini` and `rclone.conf`.
- `SKIP_PLANET=true` is the safe first-pass setting for a new host.

## When to troubleshoot here first

If the error mentions any of the following, the problem is usually configuration rather than code:

- `config/.env does not exist`
- `config.json` missing or unreadable
- `Please specify DOMAIN_DIRECT or DOMAIN_ROUNDROBIN`
- `Please add your email to LETSENCRYPT_EMAIL`
- `rclone.conf missing`
- Cloudflare or Telegram credentials not found

If the problem is instead a runtime failure in a specific workflow, switch to that sub-skill's troubleshooting page.
