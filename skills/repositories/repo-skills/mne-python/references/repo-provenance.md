# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an MNE-Python
checkout. If the current commit, dirty state, package version, public API stubs,
metadata, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:17:12Z",
  "repository": {
    "name": "mne-python",
    "remote_url": "https://github.com/mne-tools/mne-python.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b1914e98a17f95276cd0494202c71c6ab5975f3b",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "mne",
      "version": "0.1.0.dev1+gb1914e98a",
      "import_names": ["mne"]
    }
  ],
  "evidence": {
    "source_roots": ["mne", "mne/_fiff"],
    "docs": ["README.rst", "doc/install", "doc/api", "doc/development", "CONTRIBUTING.md", "AGENTS.md"],
    "examples": ["examples", "tutorials"],
    "tests": ["mne/tests", "mne/io/*/tests", "mne/preprocessing/tests", "mne/viz/tests", "mne/time_frequency/tests", "mne/stats/tests", "mne/decoding/tests", "mne/simulation/tests"],
    "configs": ["pyproject.toml", "environment.yml", "Makefile", ".pre-commit-config.yaml"],
    "scripts": ["mne/commands", "tools/check_mne_location.py", "tools/check_changelog_names.py", "tools/check_pyproject_helpers.py", "tools/dev/generate_pyi_files.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, public `.pyi` stubs, CLI entry points, or major source
  modules changed even on the same commit, refresh the skill.
- If the checkout dirty state differs materially from this snapshot, refresh or
  verify whether the dirty paths are only generated skill artifacts.
- Optional dependency support changes in `pyproject.toml`, install docs, or
  major examples/tutorials also warrant refresh.
