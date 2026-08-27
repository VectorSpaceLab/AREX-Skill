# Deployment troubleshooting

## Purpose

Read this when the clean-server bootstrap fails before the host roles are installed.

## SSH connection failures

### Symptom

- Fabric cannot connect.
- The host prompt never appears.
- The command fails before any package install starts.

### Likely causes

- wrong hostname or SSH port
- missing or incorrect SSH key
- `SSH_PASSWD` not set when password auth is required
- the remote host is not reachable from the current machine

### Recovery

1. Verify the host is reachable with plain `ssh`.
2. Check the `.ssh/config` entry if one is expected.
3. Confirm the `hostname`, `--user`, and `--port` values.
4. Re-run with `--noninteractive` only when you already trust the host target.

## Missing `.env` values

### Symptom

- `config/.env does not exist`
- `Please specify DOMAIN_DIRECT or DOMAIN_ROUNDROBIN`
- `Please add your email to LETSENCRYPT_EMAIL`

### Likely causes

- the deployment was started without a usable `.env`
- the wrong `ENV` suffix was selected
- the user skipped the sample file

### Recovery

- start from `config/.env.sample`
- fill the domain and email fields before retrying
- use `SKIP_PLANET=true` for the first sanity pass on a new host

## Remote host not suitable

### Symptom

- the bootstrap runs but behaves unpredictably
- nginx or package setup collides with an existing system configuration
- the host has unrelated services already using the target paths

### Likely cause

The repo is designed for a clean dedicated machine or VM.

### Recovery

- move the deployment to a fresh VM or dedicated host
- avoid running this workflow on a personal dev machine

## TLS / round-robin setup failures

### Symptom

- certbot or Cloudflare steps fail
- the round-robin deploy hook cannot publish certificates
- nginx starts but certs are missing

### Likely causes

- `DOMAIN_ROUNDROBIN` is missing or wrong
- `LETSENCRYPT_EMAIL` is missing
- `cloudflare.ini` or `rclone.conf` is missing
- the host lacks the network access needed for the certificate flow

### Recovery

1. Confirm the `.env` values.
2. Confirm the Cloudflare and rclone config files.
3. Re-run the round-robin writer path only after the credentials exist.

## Venv bootstrap failures

### Symptom

- the remote virtualenv is missing or half-created
- Python packages are present but the CLI still fails

### Likely causes

- the remote venv bootstrap was interrupted
- the host already had a partially configured `/data/ofm/venv`
- the wrong Python executable was used during the remote bootstrap

### Recovery

- clean the remote venv only when you are sure the host is disposable
- re-run the deployment on a clean host
- verify the remote Python path before proceeding

## When to stop

Stop and ask for more input when the fix requires:

- a different host or fresh VM
- real SSH credentials
- real domain ownership or DNS access
- a fresh deployment config that is not yet present
