# Load-balancing API reference

## Purpose

Read this when you need the verified command and helper surface for OpenFreeMap round-robin DNS management.

## CLI command family

`loadbalancer.py` exposes these commands:

- `check`
- `fix`

## Helper signatures verified from source

| Helper | Signature | Role |
| --- | --- | --- |
| `check_or_fix` | `(fix=False)` | Run the host-health check or the repair path. |
| `run_area` | `(area)` | Check the deployed version for one area across all configured hosts. |
| `update_records` | `(working_hosts) -> bool` | Replace the Cloudflare A records with the healthy host set. |
| `telegram_quick` | `(message)` | Send a status alert. |
| `get_zone_id` | `(domain, cloudflare_api_token: str)` | Resolve the Cloudflare zone id for the configured root domain. |
| `get_dns_records_round_robin` | `(zone_id, cloudflare_api_token: str) -> dict` | Read the current A records for the round-robin domain. |
| `set_records_round_robin` | `(zone_id, *, name: str, host_ip_set: set, ttl: int = 1, proxied: bool, comment: str = None, cloudflare_api_token: str) -> bool` | Replace the A records for the target name. |
| `delete_record` | `(zone_id, *, id_: str, cloudflare_api_token: str)` | Remove a single DNS record. |
| `check_host_version` | `(domain, host_ip, area, version)` | Verify that a host serves a specific version. |
| `check_host_latest` | `(domain, host_ip, area, version)` | Verify that a host serves the latest style and versioned tile endpoints. |
| `check_tilejson` | `(url, domain, host_ip, version)` | Confirm the TileJSON points at the expected version. |
| `pycurl_status` | `(url, domain, host_ip)` | Perform a host-resolved HTTPS HEAD check. |
| `pycurl_get` | `(url, domain, host_ip)` | Perform a host-resolved HTTPS GET check. |

## Configuration and path facts

The load-balancing workflow uses:

- `HTTP_HOST_LIST`
- `DOMAIN_ROUNDROBIN`
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`
- `config/cloudflare.ini`
- `config/rclone.conf`

## Command meaning

- `check` probes all configured hosts and reports whether they serve the expected version.
- `fix` does the same probe and then rewrites the Cloudflare A records when the healthy host set changed.

## Host-check behavior to remember

- The checker uses the deployed version marker for each area.
- During the first few minutes after a deploy, the checker uses a relaxed mode.
- `fix` has a fail-safe that reverts to the full host list if no healthy hosts are detected.

## When to read this versus the workflow reference

- Read `workflows.md` for the one-time setup path and the recurring cron loop.
- Read this file when you need exact helper signatures or Cloudflare record semantics.
- Read `troubleshooting.md` when the host list, Cloudflare token, Telegram token, or deploy hook fails.
