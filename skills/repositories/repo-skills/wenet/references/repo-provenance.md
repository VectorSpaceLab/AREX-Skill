# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
WeNet. If the current repo commit, dirty state, package metadata, entry points,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T16:45:39Z",
  "repository": {
    "name": "wenet",
    "remote_url": "https://github.com/wenet-e2e/wenet.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a54b90bc768679bd4217e4c7765c0671fbfb3a7a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "wenet",
      "version": "0.0.0",
      "import_names": ["wenet"]
    }
  ],
  "evidence": {
    "source_roots": ["wenet/"],
    "package_metadata": ["setup.py", "setup.cfg", "requirements.txt"],
    "docs": ["README.md", "docs/python_package.md", "docs/train.rst", "docs/tutorial_aishell.md", "docs/tutorial_librispeech.md", "docs/runtime.md", "docs/production.rst", "docs/jit_in_wenet.md", "docs/lm.md", "docs/context.md"],
    "examples": ["examples/*/*/README.md", "examples/*/*/run*.sh", "examples/*/*/conf/*"],
    "tools": ["tools/*.py", "tools/*.sh", "tools/*.pl", "tools/fst/*", "tools/k2/*", "tools/websocket/*"],
    "runtime": ["runtime/README.md", "runtime/*/README.md", "runtime/core/", "runtime/gpu/"],
    "tests": ["test/test_file_utils.py", "test/wenet/dataset/", "test/wenet/text/", "test/resources/dataset/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, console entry points, model directory requirements, or
  public CLI/API signatures changed, refresh the skill even on the same commit.
- If training recipes, export scripts, runtime platform docs, or data schemas
  changed, refresh the relevant sub-skills.
- The snapshot was generated from a checkout already containing `skills/`
  production artifacts; do not treat the generated skill directory itself as
  source evidence for WeNet behavior.
