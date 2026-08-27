# Dataset layout and root resolution

## Root contract

Keep the three roots separate:

- `NUPLAN_DATA_ROOT` is the parent of `nuplan-v1.1`. It owns split databases
  and the `nuplan-v1.1/sensor_blobs` tree.
- `NUPLAN_MAPS_ROOT` owns the map-version metadata JSON and location packages.
  The normal package is `nuplan-maps-v1.0.json`.
- `NUPLAN_EXP_ROOT` is writable experiment/cache output. It is not a DB, map,
  or sensor root.

The standard configuration derives these paths:

```text
<data-root>/
├── maps/
│   ├── nuplan-maps-v1.0.json
│   ├── sg-one-north/<location-version>/map.gpkg
│   ├── us-ma-boston/<location-version>/map.gpkg
│   ├── us-nv-las-vegas-strip/<location-version>/map.gpkg
│   └── us-pa-pittsburgh-hazelwood/<location-version>/map.gpkg
└── nuplan-v1.1/
    ├── splits/
    │   ├── mini/*.db
    │   └── trainval/*.db
    ├── test/*.db
    └── sensor_blobs/<log-name>/<channel>/<blob-file>
```

`NUPLAN_DATA_ROOT` and `NUPLAN_MAPS_ROOT` may be overridden explicitly for a
run. `NUPLAN_MAP_VERSION` normally selects `nuplan-maps-v1.0`. The challenge
configuration uses `nuplan-v1.1/test/`; mini and trainval use
`nuplan-v1.1/splits/mini/` and `nuplan-v1.1/splits/trainval/` respectively.

The scenario builder's `data_root` parameter is a load path, not necessarily
the environment root: its bundled configs pass the split directory, and its
`db_files=None` behavior scans that directory for direct-child `.db` files.
When an explicit `db_files` file, directory, or list is supplied, that input
controls DB discovery. A DB basename used in `ScenarioFilter.log_names` omits
`.db`.

## Sensor path resolution

`image.filename_jpg` and `lidar_pc.filename` are DB-relative keys. Resolve them
by joining the exact value to
`<data-root>/nuplan-v1.1/sensor_blobs` (or the explicit `sensor_root`) and
checking that the result is a regular file. Do not derive a blob path from a
token, channel guess, or DB basename. The normal camera channels are
`CAM_F0`, `CAM_B0`, `CAM_L0`, `CAM_L1`, `CAM_L2`, `CAM_R0`, `CAM_R1`, and
`CAM_R2`; the merged lidar channel is `MergedPointCloud`.

A validator success is bounded evidence: it proves the selected DBs and sampled
referenced keys exist, not that every image or point cloud in a large archive
is intact. A missing optional sensor root should be reported as an incomplete
local layout; do not fabricate blobs or silently switch to another split.

## Map metadata and package paths

The metadata JSON is an object keyed by location. Each location entry contains
a `version`, and the local package path is computed exactly as:

```text
<maps-root>/<location>/<metadata[location].version>/map.gpkg
```

The four standard location names are `sg-one-north`, `us-ma-boston`,
`us-nv-las-vegas-strip`, and `us-pa-pittsburgh-hazelwood`. A DB's
`log.location` identifies one of these locations. The DB `log.map_version`
value is the map name used by scenario SQL and `ScenarioFilter.map_names`; it
is not the package filename `nuplan-maps-v1.0.json`. Compare both values
instead of renaming directories to make them match.

## Read-only validation

Run the bundled standard-library validator before importing heavier nuPlan
modules:

```bash
python scripts/validate_nuplan_data_root.py \
  --data-root "$NUPLAN_DATA_ROOT" \
  --maps-root "$NUPLAN_MAPS_ROOT" \
  --split mini \
  --db-limit 5 \
  --json
```

It checks local directories, metadata, expected `map.gpkg` locations, SQLite
schema, log identity, and optionally a bounded sample of sensor keys. It opens
SQLite with `mode=ro`, never contacts S3/HTTP, and does not create cache or lock
files. Exit status is `0` for no errors, `1` for missing/invalid layout, `2`
for argparse usage errors, and `3` for an unexpected validator failure. Use
`--db-limit 0` to inspect every discovered DB and `--skip-sensors` for a
DB/map-only check. The validator intentionally does not recursively scan or
repair a dataset.
