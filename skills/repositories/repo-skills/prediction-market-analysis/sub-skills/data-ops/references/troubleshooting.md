# Data-Ops Troubleshooting

## `zstd` or a downloader is missing

Symptoms:
- The download/extract helper aborts immediately.
- The script asks for a tool that is not installed.

Likely cause:
- The host does not have `zstd` and/or a supported downloader.

Recovery:
- Install `zstd` and one of `aria2c`, `curl`, or `wget` with the system package manager.
- If you need the interactive tool installer, use it only when host mutation is acceptable.

## Download or extraction fails partway through

Symptoms:
- A partial archive remains.
- The dataset is incomplete or the sentinel file is absent.

Likely cause:
- Network interruption, mirror problems, or disk exhaustion.

Recovery:
- Remove the partial archive if it is obviously corrupted.
- Confirm you have enough disk space before retrying.
- Retry only after the download source is reachable again.

## Packaging succeeds, but the source tree is still present

Symptoms:
- `data.tar.zst` exists, but `data/` was not removed.

Likely cause:
- This is the actual code behavior, not a failure.

Recovery:
- If you want to prune `data/`, do it explicitly after checking the archive.

## Archive extraction looks wrong

Symptoms:
- Expected directories or helper files are missing after extraction.

Likely cause:
- The archive was produced from a partial or stale `data/` tree.

Recovery:
- Rebuild the archive from a known-good source tree.
- Compare the extracted layout with the data-layout reference before proceeding.
