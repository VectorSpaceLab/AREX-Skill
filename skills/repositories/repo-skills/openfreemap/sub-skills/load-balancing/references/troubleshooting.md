# Load-balancing troubleshooting

## Purpose

Read this when round-robin health checks, Cloudflare updates, or the cert deploy hook fail.

## Empty or wrong host list

### Symptom

- `No hosts found on list, terminating`
- the checker reports no healthy hosts even though the host should be up

### Likely causes

- `HTTP_HOST_LIST` is empty
- the host list contains the wrong IPs
- the `config.json` used by the load balancer does not match the current deployment

### Recovery

1. Check the `.env` values.
2. Regenerate the runtime config.
3. Re-run `check` before trying `fix`.

## Cloudflare API failures

### Symptom

- zone lookup fails
- DNS record replacement fails
- the records do not change even though the host set changed

### Likely causes

- `cloudflare.ini` is missing or malformed
- the Cloudflare API token is invalid
- the zone name does not match the configured root domain

### Recovery

- verify the token and zone name
- confirm the domain in the config matches the actual zone
- retry the command after the credential file is fixed

## Telegram notification failures

### Symptom

- the DNS update works but no alert arrives
- a status message prints an API error

### Likely causes

- `TELEGRAM_TOKEN` is missing
- `TELEGRAM_CHAT_ID` is missing
- the bot cannot post to the target chat

### Recovery

- confirm the bot token and chat id
- retry the command after the messaging credentials are fixed

## Deploy-hook failures

### Symptom

- the round-robin certificate writer cannot copy the renewed cert/key
- the upload step cannot reach the bucket

### Likely causes

- `RENEWED_LINEAGE` or `RENEWED_DOMAINS` is missing in the hook environment
- `RCLONE_CONFIG` is not pointed at the right config file
- the bucket path does not exist yet

### Recovery

- use the bundled hook only in the certbot deploy-hook context
- confirm the expected certbot environment variables are present
- confirm the bucket path and rclone remote definition

## Host-check failures

### Symptom

- a host unexpectedly fails the health check
- the checker passes for some hosts but not others

### Likely causes

- the host is still deploying and the relaxed-mode window has not settled yet
- the host does not serve the expected version marker
- the tile or style endpoint on that host returns a non-200 status

### Recovery

- wait for the deploy to settle if the change was just published
- re-run `check`
- only use `fix` once you are confident the failing host really should be removed

## When to stop

Stop and ask for more input when the fix needs:

- real Cloudflare credentials
- a real Telegram bot token
- a corrected host list
- confirmation of the intended round-robin domain
- a new certificate deploy hook run on a live host
