# Workspace and split layout

## Canonical roots

A practical workspace separates the project, experiment outputs, maps, and
OpenScene assets:

```text
<workspace>/
├── navsim-project/                 NAVSIM project/install root
├── exp/                             NAVSIM_EXP_ROOT
└── dataset/                         OPENSCENE_DATA_ROOT
    ├── navsim_logs/
    │   ├── mini/                    OpenScene metadata/log pickles
    │   ├── trainval/
    │   ├── test/
    │   └── private_test_hard/      when private original metadata is used
    ├── sensor_blobs/
    │   ├── mini/                    original camera/LiDAR blobs
    │   ├── trainval/
    │   ├── test/
    │   └── private_test_hard/
    ├── navhard_two_stage/
    │   ├── openscene_meta_datas/
    │   ├── sensor_blobs/
    │   ├── synthetic_scene_pickles/
    │   └── synthetic_scenes_attributes.csv
    ├── warmup_two_stage/
    │   ├── openscene_meta_datas/    if supplied by the bundle
    │   ├── sensor_blobs/
    │   ├── synthetic_scene_pickles/
    │   └── synthetic_scenes_attributes.csv
    └── private_test_hard_two_stage/
        ├── openscene_meta_datas/
        └── sensor_blobs/
```

Maps live at `NUPLAN_MAPS_ROOT`, normally as a sibling dataset directory:

```text
<maps-root>/
└── ... nuPlan map database for nuplan-maps-v1.0 ...
```

The exact archive extraction names can vary. What matters to NAVSIM is that
the configured log directory contains the metadata files, each configured
sensor root contains paths referenced by those metadata files, and the map
root is readable by the nuPlan map API. Do not point original sensor loading
at a synthetic sensor root or point a metric cache at raw sensor data.

## Path interpolation

The standard path mapping is:

```text
navsim_log_path    = $OPENSCENE_DATA_ROOT/navsim_logs/<data_split>
original_sensor_path = $OPENSCENE_DATA_ROOT/sensor_blobs/<data_split>
metric_cache_path  = $NAVSIM_EXP_ROOT/metric_cache
```

For standard OpenScene configs, `<data_split>` is `mini`, `trainval`, or
`test`. `navtrain` uses `trainval`; `navtest`, `navhard_two_stage`, and the
other public two-stage test views use original `test` logs/sensors. The private
original split uses `private_test_hard`.

Two-stage configurations additionally select a synthetic sensor root and
synthetic scene-pickle root. The bundled path defaults in this release are
navhard-oriented; warmup and private configurations must be checked for their
explicit overrides. If a run says synthetic scenes are included, both the
matching synthetic scene directory and its matching sensor root must be
present. A missing synthetic scene directory is a setup failure, not a reason
to disable the filter silently.

## Split selection matrix

| Requested config view | Original `data_split` | Additional assets | Intended use |
|---|---|---|---|
| `mini`, `navmini` | `mini` | none beyond original logs/sensors and maps | demo/quick checks; `navmini` is filtered |
| `trainval` | `trainval` | full trainval sensors unless the agent needs only a subset | OpenScene training/validation |
| `navtrain` | `trainval` | filtered navtrain sensors may replace full sensor history; complete trainval logs still required | standardized training |
| `test`, `navtest` | `test` | none beyond original test assets | OpenScene or filtered NAVSIM v1 testing |
| `navhard_two_stage` | `test` | navhard synthetic metadata/pickles/sensors | NAVSIM v2 local pseudo closed-loop testing |
| `warmup_two_stage` | `test` | warmup synthetic bundle and its original assets | warmup leaderboard validation |
| `private_test_hard_two_stage` | `private_test_hard` | private two-stage metadata/sensors as specified by the challenge bundle | challenge submission generation |

The standard OpenScene roots are downloadable log sets; filtered NAVSIM views
are scene filters over those logs and may overlap. `navtrain` is not a
replacement for the complete `trainval` logs. The smaller navtrain sensor
bundle is useful only with those logs and should not be combined with an
unrelated split.

For competition policy, do not train on `test`, `navtest`,
`navhard_two_stage`, `warmup_two_stage`, or `private_test_hard_two_stage`.
Document any permitted external data or pretrained weights in the required
technical report.

## Acquisition and integrity

The project download helpers are reference-only for this skill. They encode
archive names and extraction layout, but they also perform network downloads,
archive extraction, and deletion. Recreate the layout manually or use a
reviewed downloader; never run an unreviewed helper as part of validation.

For the documented navtrain archives, verify MD5 before extraction or after
preserving the archive files. The expected pairs are:

```text
6f92f38d5f03ed852da7872a7122bdd2  navtrain_current_1.tgz
7a72f0a758b5df6cbe4c565920a4869f  navtrain_current_2.tgz
b083fce1428308abb5682a1a150cc1af  navtrain_current_3.tgz
68354ac2c993aa1ebbfac59547fdb840  navtrain_current_4.tgz
dc46ed34d92d5ab9cc1464d67b72fbf6  navtrain_history_1.tgz
fab177bdb79c0c9536da1566d13e5995  navtrain_history_2.tgz
71ed9a2387edc3849921861d7873c7f0  navtrain_history_3.tgz
2cc13aced2f458e50fe4cc2f26d18e07  navtrain_history_4.tgz
```

Check with `md5sum -c` and expect `OK` for every archive. On mismatch,
retain the archive and redownload only the affected artifact through an
approved channel; do not use a cleanup command that deletes all archives.

## Read-only validation example

```bash
python scripts/validate_workspace.py \
  --split navhard_two_stage --require-files
```

The command should report the five environment variables, maps, original log
and sensor roots, and the selected synthetic roots as `OK`, ending with
`VALIDATION PASSED`. `--require-files` additionally requires regular files in
the selected log/sensor roots; it does not require an experiment root to
already contain outputs. Without that flag, it checks roots and reports
missing paths without inspecting archive contents; this is useful for a
synthetic directory fixture.
