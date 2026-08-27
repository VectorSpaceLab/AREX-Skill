# HTTP-host workflows

## Purpose

Read this when you need the maintenance sequence for an already deployed OpenFreeMap HTTP host.

## Recommended sequence

1. Download or refresh the btrfs image for the target area.
2. Download assets if the styles or sprites changed.
3. Mount the available btrfs images.
4. Fetch deployed version markers.
5. Regenerate nginx config.
6. Run the sync loop or the one-shot debug path.
7. Clean old runs when the host has accumulated too many versions.

## Typical commands

HTTP-host CLI command family:

```text
download-btrfs monaco --version latest
download-assets
mount
fetch-versions
nginx-config
sync --force
auto-clean
```

If you only need to inspect the current version map, use `debug`.

## Version selection rules

- `latest` means the newest version available in the bucket.
- `deployed` means the version currently referenced by the deployed-version marker.
- A literal version string must already exist in the bucket index.

## Runtime path reminders

- Btrfs images live under `/data/ofm/http_host/runs/<area>/<version>/`.
- Assets live under `/data/ofm/http_host/assets/`.
- Mounted data is exposed under `/mnt/ofm/`.
- nginx config and certs are written under `/data/nginx/`.

## What the sync loop actually does

The sync loop:

- checks deployed version files
- downloads assets when their size changes
- downloads the latest and deployed btrfs images
- cleans stale runs
- mounts the active image set
- writes nginx config
- reloads nginx when needed

If the config says to skip the planet download, the sync loop only keeps the monaco path healthy.

## Safe first-pass advice

On a new host, first validate the quick direct-host path before waiting for the full planet download to finish. That keeps the maintenance loop easy to debug.

## When to escalate

If the request is actually about generating new tiles or changing DNS records, route it to the sibling tile-generation or load-balancing sub-skill instead of stretching the HTTP-host workflow.
