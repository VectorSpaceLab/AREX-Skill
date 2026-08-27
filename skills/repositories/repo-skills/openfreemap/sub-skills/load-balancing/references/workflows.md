# Load-balancing workflows

## Purpose

Read this when you need the round-robin DNS and certificate publishing workflow.

## 1. One-time writer setup

Use the one-time writer path when the round-robin domain is first introduced or when the certificate publish hook needs to be recreated.

The setup expects:

- `DOMAIN_ROUNDROBIN`
- `LETSENCRYPT_EMAIL`
- `cloudflare.ini`
- `rclone.conf`

The deployment CLI installs the publish hook and then requests the certificate with the Cloudflare DNS challenge.

## 2. Recurring health checks

The recurring path is the cron-driven `check` command.

It:

- reads the deployed version for each area
- probes every configured host using host-resolved HTTPS requests
- reports whether the host set is healthy
- sends Telegram alerts when the state changes

## 3. Repair path

Use `fix` when the host set needs to be rewritten.

The repair path:

1. probes the same host set as `check`
2. computes the healthy host subset
3. rewrites the Cloudflare A records for the round-robin domain
4. sends a Telegram alert when the records changed

## 4. Certificate publish hook

The certificate hook is the small shell helper that copies the renewed certificate and key into the bucket path used by the round-robin setup.

Treat it as the deploy-hook payload, not as a general-purpose upload script.

## Cron shape

The repo's cron file runs the `check` path every minute. The `fix` path is available but is intentionally not the default cron action.

## Troubleshooting cues

If the workflow behaves strangely, the usual cause is one of these:

- the host list is empty
- the Cloudflare token is missing or wrong
- the Telegram token or chat id is missing
- the deploy-hook env variables are not present
- the round-robin domain is not configured

For detailed recovery steps, switch to `references/troubleshooting.md`.
