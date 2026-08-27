# Tile-generation workflows

## Purpose

Read this when you need the end-to-end tile pipeline for OpenFreeMap.

## 1. Choose the area

OpenFreeMap uses two area names:

- `monaco`
- `planet`

`monaco` is the smaller and faster path; `planet` is the full production path.

## 2. Generate a run

Tile-generation CLI command family:

```text
make-tiles monaco
```

Add `--upload` when you want the run uploaded after generation completes.

The command:

- downloads the needed data
- runs Planetiler
- writes the MBTiles result
- converts the result into Btrfs images
- shrinks the final image
- gzips the output

## 3. Upload a finished run

If a run already exists and you only want to publish it:

Tile-generation CLI command family:

```text
upload-area monaco
```

This path expects exactly one run directory for the area.

## 4. Refresh bucket indexes

Tile-generation CLI command family:

```text
make-indexes
```

This regenerates the `dirs.txt` and `files.txt` index files for the buckets used by the tile pipeline.

## 5. Promote a version

Tile-generation CLI command family:

```text
set-version monaco --version latest
```

Use this only after the run exists in the bucket and the host checks pass.

## 6. Understand the Btrfs conversion step

The conversion stage is not just a rename. It:

1. extracts MBTiles into a hard-linked tree
2. copies/rsyncs into a second Btrfs image
3. shrinks the second image
4. gzips the final Btrfs artifact

That means the workflow is disk-heavy, root-heavy, and not a good fit for casual local machines.

## 7. Expected order on a large host

1. ensure the host has the required disk and RAM
2. ensure Java and Planetiler are available
3. ensure `rclone` is configured
4. run `make-tiles`
5. upload the finished run
6. refresh the indexes
7. promote the version only after the host checks succeed

## When to treat a step as complete

- `make-tiles`: complete when the final `tiles.btrfs.gz` and `tiles.mbtiles` outputs are written.
- `upload-area`: complete when the bucket has one finished run and a `done` marker.
- `make-indexes`: complete when the bucket index files are regenerated.
- `set-version`: complete when the deployed version marker matches the newly published run.

## Troubleshooting cues

If the pipeline fails, the usual cause is one of these:

- not enough disk or RAM
- missing root privileges
- missing `rclone`
- missing Btrfs tooling
- Planetiler or Java not installed
- attempting to upload before exactly one finished run exists

For details, switch to `references/troubleshooting.md`.
