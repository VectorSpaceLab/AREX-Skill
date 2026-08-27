---
name: data-ops
description: "Guide dataset download, extraction, and packaging workflows for
  prediction-market-analysis."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# data-ops

Use this sub-skill for dataset download, extraction, archive creation, and host-tool troubleshooting.
It covers the repo's dataset lifecycle but not the analysis or indexing logic.

## Use this route when

- The user wants to download or restore the prebuilt dataset.
- The user wants to package `data/` into `data.tar.zst`.
- The user needs to diagnose `zstd`, downloader, or archive problems.
- The user wants to understand the repo's `make setup` or `make package` behavior.

## Scope

### Included

- Dataset download and extraction from the published archive.
- Packaging `data/` into `data.tar.zst`.
- Host-tool and network troubleshooting for those workflows.
- Archive and sentinel-file behavior.

### Excluded

- Market/trade/block backfills, which belong to `sub-skills/indexing/`.
- Analysis and plotting workflows, which belong to `sub-skills/analysis/`.

## Read first

- `../../references/data-ops.md` for the workflow summary.
- `../../references/data-layout.md` for the directories the dataset should contain.
- `../../references/troubleshooting.md` for cross-cutting failures.

## Core workflow

1. Determine whether the user wants to download/extract or package.
2. Check the required host tools and disk space.
3. Run the download/extract or packaging command from the repo checkout.
4. Verify the resulting `data/` tree or `data.tar.zst` archive.
5. If the workflow fails, use the host-tool or archive troubleshooting notes before retrying.

## Download and extract

The documented path uses `make setup`, which in turn runs the tool-install and download helpers.
Important details:

- `scripts/install-tools.sh` is interactive and may mutate the host.
- `scripts/download.sh` depends on a downloader and `zstd`.
- The archive is large, so timeouts and partial downloads are common failure points.
- A `.download_complete` sentinel marks a successful extraction cycle.

## Packaging

The packaging path is `make package` or `uv run main.py package`.
Important details:

- The archive name is `data.tar.zst`.
- The helper uses `tar --zstd`.
- The code does not remove `data/` after packaging, even though the README wording suggests that behavior.

## Adding or fixing data-ops guidance

- Keep host mutation and network side effects explicit.
- Prefer safe read-only checks before suggesting a download or package rerun.
- Make the archive and sentinel-file semantics obvious.
- Document the exact failure symptoms that mean the host is missing tools rather than the repo being broken.

## Common failure patterns

- Missing `zstd` or downloader tools.
- Not enough disk for the archive or extracted dataset.
- Download links that are temporarily unavailable.
- Confusion about whether packaging should delete the source tree.

## Helpful helper

- `../../scripts/package_data.sh` runs the packaging command from the repo root when the repo environment is available.
