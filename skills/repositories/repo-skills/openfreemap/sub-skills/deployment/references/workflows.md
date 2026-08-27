# Deployment workflows

## Purpose

Read this when you need the order of operations for a clean OpenFreeMap server bootstrap.

## 1. Prepare the remote host

The repo assumes a dedicated Ubuntu machine or VM with sudo access.

Before running anything destructive:

- confirm SSH access to the host
- confirm the host is not a personal dev machine
- confirm the target domain and email values in `.env`
- decide whether the first pass should skip the planet download

## 2. First-pass HTTP host

A safe first pass is:

Deployment CLI command family:

```text
http-host-static HOSTNAME
```

Use this path when you want to bring up the direct HTTP host without waiting for the full planet download.

If you want the autoupdate cron file installed on the host, use `http-host-autoupdate` instead.

## 3. Full HTTP host refresh

After the first pass is healthy:

1. update the `.env` file so the deployment wants the full planet workflow
2. run the same HTTP-host command again
3. check the curl commands printed by the script
4. confirm the server returns `HTTP/2 200` on a known style or tile URL

## 4. Tile-generation host

Use:

Deployment CLI command family:

```text
tile-gen HOSTNAME
```

Use `--cron` if the host should install the recurring cron entry, and `--reinstall` if the host data under `/data/ofm` should be rebuilt.

The tile-generation path is only appropriate for a large, dedicated machine.

## 5. Load-balancing host

Use:

Deployment CLI command family:

```text
loadbalancer HOSTNAME
```

This installs the DNS health-checking workflow and its cron entry.

## 6. Round-robin certificate publishing

Use:

Deployment CLI command family:

```text
roundrobin-dns-writer HOSTNAME
```

This is the one-time path that prepares the Cloudflare DNS challenge and publishes certificates to the bucket used by the round-robin host setup.

## 7. Direct sync or debug runs

- `http_host_sync` runs the HTTP-host sync command without the broader bootstrap.
- `debug` runs the sync path without the confirmation gate.

## Deployment order to remember

1. shared user + base packages
2. shared config and venv bootstrap
3. HTTP-host or tile-generation runtime files
4. cron files only when the host should stay updated automatically
5. verification curl checks after the first HTTP-host pass

## Troubleshooting cues

If this workflow fails, the usual root cause is one of these:

- the host was not a clean Ubuntu machine
- the SSH connection or user was wrong
- the `.env` file was incomplete
- the host lacked sudo or package-manager access
- the user skipped the temporary `SKIP_PLANET=true` pass on a machine that needed it

For detailed recovery steps, switch to `references/troubleshooting.md`.
