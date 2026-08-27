# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Hail. If the current repo commit, dirty state, package metadata, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T18:51:09Z",
  "repository": {
    "name": "hail",
    "remote_url": "https://github.com/hail-is/hail",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1458d959ca4b23ce784dffff7dae69e7dbb5ab22",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The checkout had an untracked skills/ tree during skill generation; generated skill files are under skills/."
  },
  "packages": [
    {
      "name": "hail",
      "version": "0.2.138",
      "import_names": ["hail", "hailtop"],
      "console_scripts": ["hailctl"]
    }
  ],
  "evidence": {
    "source_roots": [
      "hail/python/hail",
      "hail/python/hailtop"
    ],
    "package_metadata": [
      "hail/python/setup.py",
      "hail/python/requirements.txt",
      "hail/python/hailtop/requirements.txt",
      "hail/build.mill"
    ],
    "docs": [
      "README.md",
      "hail/python/hail/docs",
      "hail/python/hailtop/batch/docs"
    ],
    "tests": [
      "hail/python/test/hail",
      "hail/python/test/hailtop"
    ],
    "scripts_considered": [
      "hail/scripts",
      "hail/python/cluster-tests",
      "hail/python/benchmark"
    ],
    "existing_skill_evidence": [
      "skills/disco/hail"
    ],
    "excluded_major_areas": [
      "auth",
      "batch",
      "ci",
      "gear",
      "monitoring",
      "web_common",
      "website",
      "infra",
      "docker",
      "gateway",
      "internal-gateway",
      "bootstrap-gateway",
      "letsencrypt",
      "prometheus",
      "grafana",
      "tls"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is clean but this snapshot was dirty, or if the dirty paths differ materially outside `skills/`, run `refresh-repo-skill` when source evidence changed.
- If `hail/python/setup.py`, `hail/python/requirements.txt`, `hail/python/hailtop/requirements.txt`, `hail/build.mill`, public `hail`/`hailtop` APIs, or `hailctl` command families changed, run `refresh-repo-skill`.
- If generated package files such as `hail/version.py`, `hailtop/version.py`, or backend JAR assets are missing in a raw checkout, inspect an installed package or build output before deciding that public APIs disappeared.
