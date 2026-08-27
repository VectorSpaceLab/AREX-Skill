# Data Operations

This repo has two distinct data-ops workflows:

1. Download and extract the prebuilt dataset.
2. Package the current `data/` tree into `data.tar.zst`.

Use this page when the task is about the dataset itself, not the analysis or indexer logic.

## Download and extract

The documented download flow is:

1. Ensure `zstd` is available.
2. Ensure at least one downloader is available: `aria2c`, `curl`, or `wget`.
3. Download `data.tar.zst`.
4. Extract it into `data/`.
5. Record completion with the `.download_complete` sentinel.

Important details:

- `scripts/download.sh` is network-dependent and should be treated as a host-side helper, not a safe offline runtime script.
- `scripts/install-tools.sh` is interactive and mutates the host by prompting to install `zstd` and `aria2c`.
- The archive is large, so download failures are often bandwidth or mirror issues rather than repo bugs.

## Package the dataset

The packaging code is in `src/common/util/package.py` and is reached through `main.py package` or `make package`.

Behavior:

- Packages `data/` into `data.tar.zst` using `tar --zstd`.
- Returns success or failure as a boolean and exits accordingly through `main.py`.
- Does **not** delete the source `data/` directory, even though the README text implies removal.

## What to expect from the archive

- The archive should preserve the `data/kalshi/` and `data/polymarket/` subtrees.
- Cursor files and collateral lookup JSON may also be present depending on what was packaged.
- Analysis and indexer workflows assume the unpacked directory layout described in `data-layout.md`.

## When this workflow fails

- Missing `zstd` or downloader tools.
- Network blockage to the archive host.
- Extraction into a directory with insufficient disk space.
- Confusion about whether packaging removes the source directory.

Read `sub-skills/data-ops/references/troubleshooting.md` for concrete recovery steps.
