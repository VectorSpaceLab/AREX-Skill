---
name: tile-generation
description: "Routes OpenFreeMap tile-generation, MBTiles extraction, Btrfs
  conversion, upload, and version-promotion tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tile generation

Use this route when the task is about creating or publishing new OpenFreeMap tile runs.

This sub-skill assumes the host already has the OpenFreeMap deployment primitives in place and focuses on the tile pipeline itself: Planetiler, MBTiles extraction, Btrfs conversion, upload, and version promotion.

## Typical triggers

- "make tiles for planet"
- "run the tile generator"
- "upload a monaco run"
- "create indexes for the bucket"
- "promote a version"
- "convert MBTiles into a deduplicated Btrfs tree"

## What this route covers

- Planetiler execution for `planet` and `monaco`.
- Converting MBTiles into a hard-linked directory tree.
- Creating, uploading, and versioning Btrfs tile runs.
- Uploading a finished run and refreshing bucket indexes.
- Knowing when the Btrfs shrink helper is reference-only.

## What this route does not cover

- Host bootstrap or SSH setup.
- The HTTP-host sync and nginx refresh loop.
- DNS record management or certificate publishing.

Route those tasks to:

- `../deployment/SKILL.md`
- `../http-host/SKILL.md`
- `../load-balancing/SKILL.md`

## Read next

- `references/api-reference.md` — verified helper signatures and command families.
- `references/workflows.md` — the end-to-end tile pipeline.
- `references/troubleshooting.md` — Planetiler, disk, root, Btrfs, and upload failures.
- `scripts/extract_mbtiles.py` — bundled MBTiles extraction helper.

## Good first checks

1. Confirm whether the user wants `planet` or `monaco`.
2. Confirm the host has enough disk, RAM, and root access.
3. Confirm the upload bucket and rclone config are available.
4. Decide whether the request is a full generation run or only a version-promotion step.

## Runtime facts to remember

- `make-tiles` is intentionally heavy and can take a long time.
- `upload-area` expects exactly one run directory for the selected area.
- `make-indexes` refreshes the bucket index files after uploads.
- `set-version` is the promotion step that points the deployed version marker at a finished run.

## When to escalate

If the user only wants a reusable conversion helper or needs to inspect a tiny MBTiles fixture, use the bundled extraction script and the API reference. If they want to shrink Btrfs images, read the reference-only notes rather than turning that helper into a routine script.
