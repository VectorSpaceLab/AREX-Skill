# Tile-generation API reference

## Purpose

Read this when you need the verified command and helper surface for the OpenFreeMap tile pipeline.

## CLI command family

`tile_gen.py` exposes these commands:

- `make-tiles AREA [--upload]`
- `upload-area AREA`
- `make-indexes`
- `set-version AREA [--version ...]`

## Helper signatures verified from source

| Helper | Signature | Role |
| --- | --- | --- |
| `run_planetiler` | `(area: str) -> Path` | Run Planetiler for `planet` or `monaco` and return the run directory. |
| `make_btrfs` | `(run_folder: Path)` | Convert the MBTiles result into Btrfs images and supporting logs. |
| `cleanup_folder` | `(run_folder: Path)` | Remove stale mounts, logs, and intermediate outputs for a run directory. |
| `upload_area` | `(area)` | Upload the single run for an area and refresh the bucket index. |
| `upload_area_run` | `(area, run)` | Sync one run directory to the `ofm-btrfs` bucket and create the `done` marker. |
| `make_indexes_for_bucket` | `(bucket)` | Regenerate `dirs.txt` and `files.txt` for a bucket. |
| `check_and_set_version` | `(area, version)` | Validate that the target version is available and promote it when ready. |
| `set_version` | `(area, version)` | Write the deployed version marker in the assets bucket. |
| `check_all_hosts` | `(area, version) -> bool` | Confirm that all configured hosts serve the requested version. |

## Configuration and path facts

The tile-generation workflow uses:

- `/data/ofm/tile_gen/runs/`
- `/data/ofm/tile_gen/bin/`
- `/data/ofm/tile_gen/planetiler/`
- `/data/ofm/config/rclone.conf`
- the remote buckets named `ofm-btrfs` and `ofm-assets`

## Command meaning

- `make-tiles` runs Planetiler for the selected area and produces a new run.
- `--upload` on `make-tiles` uploads the finished run after generation completes.
- `upload-area` expects exactly one run directory for the selected area.
- `make-indexes` refreshes the bucket indexes after uploads.
- `set-version` writes the deployed version marker once the run is ready to promote.

## Pipeline facts worth remembering

- `run_planetiler` deletes the previous run directory for the selected area before starting a new one.
- `make_btrfs` creates the Btrfs images, extracts MBTiles, rsyncs them, shrinks the image, and gzips the final file.
- `extract_mbtiles.py` is the reusable helper that turns MBTiles into the hard-linked directory tree.
- `shrink_btrfs.py` is a reference-only helper because it needs root and mutates disk images in place.
- `check_and_set_version` first confirms that every configured host serves the target version before writing the deployed version marker.

## When to read this versus the workflow reference

- Read `workflows.md` for the full tile pipeline sequence.
- Read this file when you need exact signatures, bucket names, or helper roles.
- Read `troubleshooting.md` when a Planetiler, Btrfs, upload, or version-promotion step fails.
