---
name: http-host
description: "Routes OpenFreeMap HTTP-host maintenance tasks such as downloads,
  mounts, nginx refreshes, and sync runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HTTP host

Use this route when the task is about an already deployed OpenFreeMap HTTP host.

This sub-skill assumes the host bootstrap already happened. It focuses on the runtime maintenance loop that keeps the host serving assets, btrfs images, styles, and version metadata.

## Typical triggers

- "download the btrfs images"
- "mount the OpenFreeMap host"
- "refresh nginx"
- "run the HTTP-host sync"
- "fetch deployed versions"
- "clean old runs"
- "convert MBTiles metadata to TileJSON"

## What this route covers

- Downloading btrfs images and assets.
- Mounting and cleaning up the runtime btrfs tree.
- Fetching deployed version files.
- Regenerating nginx config and reloading nginx.
- Running the sync loop that cron calls every minute.
- The small TileJSON conversion helper used during nginx config generation.

## What this route does not cover

- Initial server provisioning or SSH user/package bootstrap.
- Tile generation and upload.
- Round-robin DNS or certificate publishing.

Route those tasks to:

- `../deployment/SKILL.md`
- `../tile-generation/SKILL.md`
- `../load-balancing/SKILL.md`

## Read next

- `references/api-reference.md` — verified helper signatures and command families.
- `references/workflows.md` — the runtime maintenance sequence.
- `references/troubleshooting.md` — missing image, mount, nginx, and config failures.
- `../../references/configuration.md` — shared config-file facts.
- `scripts/metadata_to_tilejson.py` — bundled helper used by nginx config generation.

## Good first checks

1. Confirm the host already has a generated `config.json`.
2. Confirm the host has the btrfs and asset directories the runtime expects.
3. Decide whether the task is a safe read-only check or a state-changing sync.
4. Use the workflow reference to decide whether the user wants just a single command or the full sync loop.

## Runtime facts to remember

- The host-side modules assume Linux and root privileges for mounting and nginx reloads.
- The sync path can be forced with `sync --force`.
- `download-btrfs` accepts `latest`, `deployed`, or a specific version string.
- `nginx-config` will not work until the mount step has produced the expected file tree.

## When to escalate

If the user actually wants to generate tiles or fix DNS records, hand the task to the sibling sub-skill instead of trying to stretch the HTTP-host route.
