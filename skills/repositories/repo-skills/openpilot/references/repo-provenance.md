# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an openpilot checkout. If the current checkout's commit, dirty paths, dependency metadata, submodule layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the generated guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:26:50Z",
  "repository": {
    "name": "openpilot",
    "remote_url": "https://github.com/commaai/openpilot.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "122a8ca00ab4ab78d62adeaf4fe26f7e5253815e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "openpilot",
      "version": "0.1.0",
      "import_names": ["openpilot"]
    },
    {
      "name": "opendbc",
      "version": "0.3.1",
      "import_names": ["opendbc"]
    },
    {
      "name": "msgq",
      "version": "0.0.1",
      "import_names": ["msgq"]
    }
  ],
  "submodules": {
    "msgq_repo": "0e266c1dbcf7328beee3e57b4a8688555387c877",
    "opendbc_repo": "44f2987cb6ed28f7dcd99d5930abf6c2917d8f60",
    "panda": "dd8a5b3df77706337a11555377e7180c5adc8726",
    "rednose_repo": "28d4a7f69e80e1c3e0d24ca0733d7daeaeade3d0",
    "teleoprtc_repo": "31db236a9ef820d7051ccd53488153cfbc84d3b9",
    "tinygrad_repo": "8611fe22a7fcc7d1928bbde19ded66277cb12f3e"
  },
  "evidence": {
    "source_roots": ["openpilot", "msgq_repo", "opendbc_repo", "panda", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"],
    "docs": ["README.md", "docs", "tools/README.md", "openpilot/tools/*/README.md"],
    "tools_and_scripts": ["tools", "scripts", "openpilot/tools"],
    "tests": ["openpilot/*/tests", "openpilot/test_native.py", "tools/test_runner.py"],
    "configs": ["pyproject.toml", ".python-version", "uv.lock", "SConstruct", ".gitmodules"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If submodule commits differ, especially `opendbc_repo` or `msgq_repo`, refresh car-port and messaging guidance.
- If `pyproject.toml`, `.python-version`, `uv.lock`, or `SConstruct` changes, refresh setup/build/native-extension guidance.
- If new tests, route tools, car-port helpers, simulator tools, or docs are added, refresh the relevant sub-skill.
- The recorded dirty path is the generated `skills/` output area; unrelated dirty source paths should trigger a refresh review.
