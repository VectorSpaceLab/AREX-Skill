# Tile-generation troubleshooting

## Purpose

Read this when the tile pipeline fails during Planetiler, MBTiles extraction, Btrfs conversion, upload, or version promotion.

## Planetiler or Java problems

### Symptom

- the run never starts
- `java -version` is missing or wrong
- Planetiler exits early before writing outputs

### Likely causes

- Java is not installed on the host
- the Planetiler jar is missing
- the host has too little RAM for the selected area

### Recovery

1. Confirm Java is available.
2. Confirm the Planetiler jar exists.
3. Use the smaller `monaco` workflow to verify the host before attempting the full planet path.

## Disk-space failures

### Symptom

- the run stops while downloading or uncompressing data
- Btrfs conversion fails partway through
- the host reports not enough free disk

### Likely causes

- the tile-generation host is too small
- the temporary Btrfs image and extraction tree need more space than expected
- the `planet` workflow was started on a host sized only for `monaco`

### Recovery

- use a larger dedicated machine
- free disk before retrying
- start with the smaller area first if you are just validating the workflow

## Btrfs conversion failures

### Symptom

- `make_btrfs` fails during mount, rsync, or shrink
- the final image does not get produced
- `shrink_btrfs.py` errors out on resize

### Likely causes

- missing root access
- missing `btrfs-progs`
- mount or resize tools unavailable
- the image is already in a half-built state from a previous run

### Recovery

- confirm root and Btrfs tooling
- clean the run directory before retrying
- use the script reference to understand why the shrink helper is not a generic utility

## Upload and index failures

### Symptom

- `upload-area` refuses to run
- the bucket does not get a `done` marker
- bucket indexes stay stale

### Likely causes

- more than one run directory exists for the area
- the `rclone` config is missing or wrong
- the bucket path is wrong

### Recovery

1. Ensure exactly one run exists for the area.
2. Confirm the `rclone.conf` file is present.
3. Re-run the upload and then refresh the bucket indexes.

## Version promotion failures

### Symptom

- `set-version` says the version is not available
- the host checks fail before the version marker is written

### Likely causes

- the run has not been uploaded yet
- one or more configured hosts do not serve the version
- the current version markers are stale

### Recovery

- verify the upload completed
- verify the host checks for the target area
- rerun the promotion only after the server-side checks pass

## MBTiles extraction failures

### Symptom

- `extract_mbtiles.py` fails to write the tree
- the output directory is not empty
- the deduplicated hard-link layout looks incomplete

### Likely causes

- the output directory already contained files
- the MBTiles file is malformed
- the source database lacks the expected metadata or tile tables
- the metadata is missing `osm_date` and also lacks `planetiler:osm:osmosisreplicationtime`

### Recovery

- start from an empty output directory
- confirm the MBTiles source is valid
- inspect the tiny synthetic fixture before trusting a production run

## When to stop

Stop and ask for more input when the fix needs:

- more RAM or disk than the host has
- root access on the tile-generation machine
- a new Planetiler or Java install
- a fresh upload bucket or `rclone` credential set
