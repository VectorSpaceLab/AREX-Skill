---
name: openfreemap
description: "Routes OpenFreeMap deployment, HTTP-host maintenance,
  tile-generation, load-balancing, and client-integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenFreeMap

Use this skill for OpenFreeMap repository operations: clean-server bootstrap, HTTP-host sync, tile generation, round-robin DNS maintenance, public style integration, and benchmark helpers.

## Quick install and inspection

Create a Python 3.11 environment and install the editable repo packages you need for inspection:

```bash
python -m pip install -e . -e modules/http_host -e modules/tile_gen -e modules/loadbalancer
```

OpenFreeMap's Python packages read configuration at import time. If you are inspecting a checkout before a real deployment exists, point `ENV` at `sample` so `ssh_lib` can read `config/.env.sample`, and provide a temporary `config.json` stub or deployment-generated config for the host-side modules.

Minimal safe import check:

```bash
ENV=sample python -I -c "import ssh_lib, http_host_lib.config, tile_gen_lib.config, loadbalancer_lib.config"
```

The repo does not require a GPU/accelerator backend. A single CPU-capable inspection environment is enough.

## What to read first

- `references/repo-provenance.md` — check whether this skill still matches the current checkout.
- `references/configuration.md` — read this when a task mentions `.env`, `config.json`, bucket credentials, or deployment prerequisites.
- `references/troubleshooting.md` — read this first for import/config/runtime failures.
- `references/client-integration.md` — read this for MapLibre, Mapbox migration, Leaflet, OpenLayers, mobile, or custom-style questions.
- `references/benchmarking.md` — read this for localhost benchmarking and path-list replay.

## Route map

### 1. Clean-server bootstrap and deployment

Start here when the request is about a fresh Ubuntu server, a VM, or the `init-server.py` orchestration entry point.

Follow `sub-skills/deployment/SKILL.md` for:

- SSH connection setup and confirmation prompts.
- Remote user creation, sudo setup, and package installation.
- HTTP-host, tile-generation, and load-balancing deployment entry points.
- The quick-test path with `SKIP_PLANET=true` before a full planet run.

### 2. HTTP-host runtime maintenance

Start here when the request is about downloading btrfs images, assets, version files, mounting tiles, rebuilding nginx config, or running the sync cron workflow.

Follow `sub-skills/http-host/SKILL.md` for:

- `download-btrfs`, `download-assets`, `mount`, `fetch-versions`, `nginx-config`, `sync`, `auto-clean`, and `debug`.
- `metadata_to_tilejson.py`, which is bundled as a reusable helper.
- Errors such as missing images, stale mounts, or missing deployment config.

### 3. Tile generation and publishing

Start here when the request is about Planetiler runs, MBTiles extraction, Btrfs image conversion, uploads, or version promotion.

Follow `sub-skills/tile-generation/SKILL.md` for:

- `make-tiles`, `upload-area`, `make-indexes`, and `set-version`.
- How MBTiles become deduplicated hard-linked Btrfs trees.
- Why `shrink_btrfs.py` stays reference-only instead of being wrapped as a routine helper.

### 4. Round-robin DNS and certificate publishing

Start here when the request is about Cloudflare DNS records, host-health checks, certificate deploy hooks, or round-robin public hosts.

Follow `sub-skills/load-balancing/SKILL.md` for:

- `check`, `fix`, and the one-time `roundrobin-dns-writer` setup path.
- The bundled `rclone_write.sh` deploy hook.
- Cloudflare, Telegram, and host-list troubleshooting.

## Client usage and public-instance guidance

When the task is about using OpenFreeMap in a site or app rather than operating the repo itself, read `references/client-integration.md`.

That reference covers:

- MapLibre GL JS integration.
- Mapbox-to-MapLibre migration guidance.
- Leaflet and OpenLayers adapters.
- Mobile-app usage through MapLibre Native.
- Custom styles and Maputnik-driven edits.

## Benchmarking helpers

When the task is about replaying nginx access patterns or checking localhost throughput, read `references/benchmarking.md` and use the bundled helpers in `scripts/`.

- `scripts/nginx_to_path_list.py` converts a tiny access-log sample into a replay list.
- `scripts/wrk_custom_list.lua` replays those paths with `wrk`.

## Common repo facts

- OpenFreeMap is designed for clean Ubuntu servers or dedicated VMs, not for casual local installs.
- HTTP-host and tile-generation workflows assume `/data/ofm/config/config.json` exists on the target host.
- Round-robin DNS workflows additionally need `cloudflare.ini` and `rclone.conf`.
- `MapLibre` is the preferred client integration path; Mapbox GL JS 2.x+ is not the recommended route.
- The repo ships no native test suite; safe CLI help checks and tiny synthetic fixtures are the usual verification path.

## Freshness check

Before relying on this skill for a changed checkout, read `references/repo-provenance.md`.

If the commit, branch, dirty state, or evidence roots differ from that snapshot, refresh the skill before trusting the routes or references.
