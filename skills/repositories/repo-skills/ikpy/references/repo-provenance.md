# Repository Provenance

Read this before deciding whether this skill matches a checkout of IKPy. If the
commit, dirty baseline, package version, or public evidence paths differ,
consider `refresh-repo-skill` before relying on detailed behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T20:15:16Z",
  "repository": {
    "name": "ikpy",
    "remote_url": "https://github.com/Phylliade/ikpy",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9a2d5f78a41bfd91850fb027301d21c73c766084",
    "working_tree": "dirty",
    "dirty_paths": ["skills/ikpy.log"],
    "dirty_summary": "one pre-existing untracked production log; generated skill output is not source evidence"
  },
  "packages": [
    {
      "name": "ikpy",
      "version": "4.0.0",
      "import_names": ["ikpy"]
    }
  ],
  "evidence": {
    "source_roots": ["src/ikpy"],
    "docs": ["README.md", "doc", "tutorials.md"],
    "examples": ["tutorials"],
    "tests": ["tests/test_chain.py", "tests/test_chain_dh.py", "tests/test_orientation.py", "tests/test_urdf.py", "tests/test_mjcf.py", "tests/test_jax_backend.py", "tests/test_poppy_robots.py"],
    "configs": ["pyproject.toml", "setup.cfg"],
    "fixtures": ["resources/mjcf", "resources/*.URDF", "resources/*.urdf", "resources/**/*.json"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the source dirty baseline changes, or public APIs, extras, parser modules,
  or backend behavior change, refresh before using detailed guidance.
- The runtime skill intentionally does not depend on the checkout's resources,
  tests, notebooks, scripts, or local environment. They are provenance and
  verification evidence only.
