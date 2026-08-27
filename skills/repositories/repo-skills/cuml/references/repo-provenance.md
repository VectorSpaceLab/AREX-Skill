# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a cuML checkout. If the current repository commit, dirty state, package metadata, or major public evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T18:57:21Z",
  "repository": {
    "name": "cuml",
    "remote_url": "https://github.com/rapidsai/cuml.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0d3a802b2a13811db3e6e52ef4e344c2d2adf9d2",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "cuml-cu13",
      "version": "26.10.0a69.post260815062704",
      "import_names": ["cuml"]
    },
    {
      "name": "libcuml-cu13",
      "version": "26.10.0a69.post260815062704",
      "import_names": ["libcuml"]
    },
    {
      "name": "cudf-cu13",
      "version": "26.10.0a224.post260815052040",
      "import_names": ["cudf"]
    }
  ],
  "source_package_version": "26.10.00",
  "evidence": {
    "source_roots": [
      "python/cuml/cuml",
      "python/libcuml/libcuml",
      "cpp/include",
      "cpp/src"
    ],
    "docs": [
      "README.md",
      "BUILD.md",
      "docs/source/api",
      "docs/source/user_guide.rst",
      "docs/source/advanced.rst",
      "docs/source/health_checks.rst",
      "docs/source/cuml-accel",
      "docs/source/dask_multigpu_guide.ipynb",
      "docs/source/supported_versions.rst"
    ],
    "examples": [
      "notebooks",
      "cpp/examples"
    ],
    "tests": [
      "python/cuml/tests",
      "python/cuml/cuml_accel_tests",
      "cpp/tests"
    ],
    "configs": [
      "python/cuml/pyproject.toml",
      "python/libcuml/pyproject.toml",
      "dependencies.yaml",
      "conda/environments"
    ],
    "repo_guidance": [
      "python/agents.md",
      "cpp/agents.md"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If public package metadata, API docs, `cuml.accel` compatibility tables, Dask optional dependencies, build prerequisites, or source roots changed, refresh the skill even if the commit comparison is unavailable.
- The recorded dirty path reflects generated skill/log artifacts, not a source-code modification. If a future checkout has source-code dirty paths in addition to generated artifacts, refresh before using source-specific build or API guidance.
- If the installed package major/minor RAPIDS generation differs from the source package version, verify signatures and compatibility before trusting detailed API defaults.
