# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Lux. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:23:29Z",
  "repository": {
    "name": "lux",
    "remote_url": "https://github.com/lux-org/lux.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "972e5ec24991483370dda67de6bb1e354bcf8ca6",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The checkout already contained an untracked skills area used for production artifacts before this generated runtime skill was written. Treat source code evidence paths below as the refresh baseline."
  },
  "packages": [
    {
      "name": "lux-api",
      "version": "0.5.1",
      "import_names": [
        "lux"
      ]
    }
  ],
  "evidence": {
    "package_metadata": [
      "setup.py",
      "setup.cfg",
      "pyproject.toml",
      "requirements.txt",
      "requirements-dev.txt",
      "MANIFEST.in",
      "conda.recipe/meta.yaml"
    ],
    "source_roots": [
      "lux/"
    ],
    "docs": [
      "README.md",
      "doc/index.rst",
      "doc/source/getting_started/",
      "doc/source/guide/",
      "doc/source/advanced/",
      "doc/source/reference/"
    ],
    "data_fixtures": [
      "lux/data/car.csv",
      "lux/data/college.csv"
    ],
    "tests": [
      "tests/",
      "tests_sql/"
    ],
    "source_scripts_reviewed": [
      "Makefile",
      "doc/docbuild.sh",
      "lux/data/upload_car_data.py",
      "lux/data/upload_aug_test_data.py",
      "lux/data/upload_airbnb_nyc_data.py",
      "lux/data/upload_flights_data.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public import names, class signatures, config properties, or source directories changed even on the same commit, run `refresh-repo-skill`.
- If the current checkout's dirty source files differ from this snapshot, run `refresh-repo-skill`. Generated skill artifacts under `skills/` are not source API evidence by themselves.
- SQL support was documented as optional PostgreSQL support at this snapshot. If SQL executor behavior, connector requirements, or supported databases changed, refresh the `sql-backend` sub-skill.
