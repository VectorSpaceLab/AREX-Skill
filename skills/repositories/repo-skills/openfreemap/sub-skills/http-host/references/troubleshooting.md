# HTTP-host troubleshooting

## Purpose

Read this when a deployed HTTP host cannot download, mount, sync, or render nginx config.

## Missing runtime files

### Symptom

- `download-btrfs needs to be run first`
- `mount needs to be run first`
- `mount` or `nginx-config` fails because a version directory is missing

### Likely causes

- the host was freshly provisioned and no btrfs image has been downloaded yet
- the asset sync has not populated the styles and sprite directories
- the deployment did not generate the runtime config JSON yet

### Recovery

1. Download the btrfs images first.
2. Download the assets.
3. Mount the images.
4. Re-run `nginx-config` or `sync`.

## Version download failures

### Symptom

- `No versions found for ...`
- `Requested version is not available`
- the download command returns without writing a btrfs file

### Likely causes

- the bucket has no published version yet
- the area name was wrong
- the host lacks enough free disk for the decompression step

### Recovery

- verify the area is `planet` or `monaco`
- confirm the bucket index has the requested version
- free disk space before retrying

## Mounting failures

### Symptom

- `mount -a` fails
- the fstab rewrite does not create the expected mount points
- nginx config generation cannot see the mounted `metadata.json`

### Likely causes

- missing `sudo`
- missing `btrfs-progs`
- the image file is absent or corrupt
- the host is not Linux

### Recovery

- confirm the host is Linux and the user has root access
- rerun the download step and then the mount step
- inspect `/etc/fstab` only after the runtime files exist

## nginx config failures

### Symptom

- `nginx-config` fails or nginx refuses to reload
- the TileJSON file is missing
- the style URL works for one version but not another

### Likely causes

- the mount tree is incomplete
- the generated `config.json` is missing a required field
- the host has not yet mounted the latest image set

### Recovery

1. Re-run `mount`.
2. Confirm the version directories contain `metadata.json` and `tiles/`.
3. Re-run `nginx-config`.
4. Check the generated curl test lines printed by the command.

## Asset refresh failures

### Symptom

- `download-assets` fails on fonts, styles, natural earth, or sprites
- the asset directory updates partially but the host still serves stale files

### Likely causes

- remote downloads failed or were interrupted
- the local asset directory is half-updated
- the environment is missing `aria2c` or `tar`

### Recovery

- rerun the asset download after verifying the host has network access
- confirm the helper commands are installed
- if a tarball was half-extracted, clean the asset directory before retrying

## Import/config failures

### Symptom

- `config.json` missing or unreadable
- the helper modules cannot import

### Likely causes

- the host has not been bootstrapped yet
- the user tried to import the package without a deployment-generated config

### Recovery

- use a deployment-generated `config.json`
- for read-only inspection, create a throwaway local stub only

## When to stop

Stop and escalate when the fix needs any of these:

- a fresh deployment on a clean host
- actual disk-space recovery
- remote sudo access
- real host-side network access
- a domain or certificate change
