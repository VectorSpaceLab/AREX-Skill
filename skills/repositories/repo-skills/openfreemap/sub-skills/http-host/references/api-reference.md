# HTTP-host API reference

## Purpose

Read this when you need the verified command and helper surface for OpenFreeMap HTTP hosts.

## CLI command family

`http_host.py` exposes these commands:

- `download-btrfs [AREA] [--version ...]`
- `download-assets`
- `mount`
- `fetch-versions`
- `auto-clean`
- `nginx-config`
- `sync [--force]`
- `debug`

## Helper signatures verified from source

| Helper | Signature | Role |
| --- | --- | --- |
| `download_assets` | `() -> bool` | Download and extract fonts, styles, natural earth, and sprites. |
| `download_area_version` | `(area: str, version: str) -> bool` | Download a specific `planet` or `monaco` btrfs version. |
| `download_and_extract_btrfs` | `(area: str, version: str) -> bool` | Fetch and decompress a btrfs image into the runtime tree. |
| `auto_mount` | `()` | Rebuild `/etc/fstab` entries and mount available btrfs images. |
| `create_fstab` | `()` | Rewrite the OpenFreeMap btrfs loop-mount entries. |
| `clean_up_mounts` | `(mnt_dir)` | Remove deleted or stale mounts. |
| `write_nginx_config` | `()` | Render nginx configs, rewrite style TileJSONs, and reload nginx. |
| `create_nginx_conf` | `(*, template_path, local, domain)` | Render one nginx server config from a template. |
| `create_location_blocks` | `(*, local, domain)` | Build the location blocks for all mounted versions. |
| `create_version_location` | `(*, area: str, version: str, mnt_dir, local: str, domain: str)` | Emit a specific version block and TileJSON file. |
| `create_latest_locations` | `(*, local: str, domain: str)` | Emit the latest and wildcard location blocks from deployed versions. |
| `write_roundrobin_reader_script` | `(domain_roundrobin)` | Emit the cert reader hook used by the round-robin host path. |
| `full_sync` | `(force=False)` | Run the sync loop that downloads assets, btrfs images, mounts them, and refreshes nginx. |
| `fetch_version_files` | `() -> bool` | Sync deployed version markers from the public bucket. |

## Configuration and path facts

The HTTP-host workflow uses:

- `/data/ofm/http_host/runs/`
- `/data/ofm/http_host/assets/`
- `/data/ofm/http_host/bin/`
- `/mnt/ofm/`
- `/data/nginx/sites/`
- `/data/nginx/certs/`
- `/data/nginx/acme-challenges/`

`http_host_lib.config.Configuration` also records the runtime area list and the active config directory.

## Common command meaning

- `download-btrfs` retrieves a specific version or the latest/deployed version for an area.
- `download-assets` fetches fonts, styles, natural earth, and sprites.
- `mount` rebuilds the loop mounts from the downloaded btrfs files.
- `fetch-versions` updates the deployed version markers.
- `auto-clean` removes old runs while keeping the newest and deployed versions.
- `nginx-config` regenerates nginx config from the mounted file tree.
- `sync` runs the full maintenance cycle; `--force` forces an nginx refresh even if no downloads changed.

## Key implementation facts

- `download-btrfs` refuses invalid areas and checks remote file size before downloading.
- `auto_mount` rewrites `/etc/fstab` and then runs `mount -a`.
- `write_nginx_config` uses `metadata_to_tilejson.py` to build per-version TileJSON files.
- `full_sync` can skip the planet download when the config says so.
- `write_nginx_config` also creates the `roundrobin_reader.sh` hook when round-robin config exists.

## When to read this versus the workflow reference

- Read `workflows.md` for the recommended sequence.
- Read this file when you need exact command names, signatures, or generated paths.
- Read `troubleshooting.md` when the host misses files, mounts, or runtime config.
