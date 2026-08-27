# Repository Provenance

Read this before deciding whether the OpenMC operating skill is current for a
checkout or package release. If the source revision, dirty state, public
package metadata, or major evidence paths differ, use `refresh-repo-skill`
rather than silently trusting the graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "openmc",
    "remote_url": "https://github.com/openmc-dev/openmc",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "86ceaad3cd58aa8e14f1aa6862fb60b625c6c473",
    "working_tree": "clean-for-source-snapshot; generated skill files are outside the source baseline",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "openmc",
      "version": "0.1.dev1+g86ceaad3c",
      "import_names": ["openmc", "openmc.data", "openmc.deplete", "openmc.mgxs", "openmc.model", "openmc.stats"]
    }
  ],
  "evidence": {
    "source_roots": ["openmc", "openmc/data", "openmc/deplete", "openmc/mgxs", "openmc/model", "openmc/lib", "src", "include/openmc"],
    "docs": ["README.md", "docs/source/usersguide", "docs/source/pythonapi", "docs/source/io_formats", "docs/source/methods", "docs/source/capi", "docs/source/devguide"],
    "examples": ["examples"],
    "tests": ["tests/unit_tests", "tests/regression_tests", "tests/cpp_unit_tests"],
    "configs": ["pyproject.toml", "CMakeLists.txt", "pytest.ini"]
  }
}
```

The source snapshot was clean at the commit above before this generated
`skills/` tree was written. The generated runtime and review files are not
source evidence and must not be counted as source changes when assessing API
staleness.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the source working tree is dirty in paths that affect `openmc/`, `src/`,
  `include/`, docs, examples, tests, `pyproject.toml`, or `CMakeLists.txt`,
  refresh before relying on the skill for exact behavior.
- If package version, Python minimum, public entry points, CMake options, XML or
  HDF5 formats, or optional integrations changed, refresh even if the commit is
  unchanged in a package installation.
- Re-run the package/API and native/data gates after refresh. In particular,
  never infer that `openmc.lib` is available just because base `openmc` imports.
