# Data-Ops Workflows

## Download and extract the dataset

1. Make sure the host has `zstd`.
2. Make sure at least one downloader exists: `aria2c`, `curl`, or `wget`.
3. Run the repo's setup path from the checkout.
4. Confirm the `.download_complete` sentinel and the expected `data/` subtree.

## Package the dataset

1. Confirm the `data/` tree exists and contains the files you want to archive.
2. Run `uv run main.py package` or the packaging wrapper.
3. Verify that `data.tar.zst` was written and is readable.
4. If you want to remove the source tree, do so separately and only after verifying the archive.

## Practical notes

- The download path is best treated as a host-side setup step, not a reusable library action.
- The packaging code is intentionally simple and delegates to `tar --zstd`.
- The code path does not delete `data/`, so archive creation and cleanup are separate decisions.
