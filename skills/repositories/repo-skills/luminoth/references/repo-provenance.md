# Repository Provenance

## Purpose

Read this before deciding whether the generated Luminoth skill is current for a
checkout of the repository. If the repository commit, dirty state, package
version, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T22:18:37Z",
  "repository": {
    "name": "luminoth",
    "remote_url": "https://github.com/tryolabs/luminoth.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9109d8b98bcbb0ad4e8e0c928da0b20627fa774f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "luminoth",
      "version": "0.2.4dev0",
      "import_names": ["luminoth"]
    }
  ],
  "evidence": {
    "source_roots": ["luminoth"],
    "docs": ["README.md", "docs/usage", "docs/tutorial", "docs/api", "docs/cli"],
    "examples": ["examples/sample_config.yml"],
    "tests": ["luminoth/**/*_test.py"],
    "configs": ["setup.py", "setup.cfg", "tox.ini", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  stale and refresh it.
- If the working tree is cleaner or dirtier than this snapshot, or if the dirty
  paths are different, refresh the skill.
- If the package version or public entry points change even on the same commit,
  refresh the skill.
- If you are unsure whether the current checkout matches this snapshot, run the
  root install smoke and compare the repository evidence paths.
