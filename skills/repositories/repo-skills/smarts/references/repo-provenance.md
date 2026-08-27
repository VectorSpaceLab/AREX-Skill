# Repository Provenance

Read this before using the skill against a different SMARTS checkout. If the
commit, package version, public entry points, or major evidence paths differ,
run a refresh rather than assuming this graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T03:10:00Z",
  "repository": {
    "name": "SMARTS",
    "remote_url": "https://github.com/huawei-noah/SMARTS",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c113dd7425e2ab648ef224c94df4ccfb9f732d6e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "smarts",
      "version": "2.0.1",
      "import_names": ["smarts", "cli", "envision"]
    }
  ],
  "evidence": {
    "source_roots": ["smarts", "cli", "envision"],
    "docs": ["README.md", "docs/setup.rst", "docs/quickstart.rst", "docs/sim", "docs/ecosystem", "docs/benchmarks"],
    "examples": ["examples", "docs/minimal.py"],
    "tests": ["smarts/**/tests", "cli/tests", "envision/tests", "examples/tests"],
    "configs": ["setup.cfg", "setup.py", "pyproject.toml", "requirements.txt", "smarts/engine.ini", "examples/configs"]
  }
}
```

The source commit is clean in the tracked repository but the checkout already
contained an untracked `skills/` production area; the generated graph is kept
under `skills/disco/smarts/` and should not be confused with upstream SMARTS
source.

## Refresh check

- If `git rev-parse HEAD` differs from `c113dd7425e2ab648ef224c94df4ccfb9f732d6e`, refresh.
- If the current `skills/` dirty state is absent or materially different, treat
  the provenance comparison as a source checkout check, not a package change.
- Refresh when `setup.cfg` changes package version, extras, entry points, or
  Python support, or when the public modules and CLI commands change.
- Re-check optional integrations separately; this baseline intentionally does
  not claim SUMO/ROS/Waymo/Argoverse/Ray/RLlib/Torch/TensorFlow training or a
  live Envision session.
