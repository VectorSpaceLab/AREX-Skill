# Repository Provenance

Read this before deciding whether the operating graph is current for another
checkout. If the pinned commit, dirty state, public entry points, or major
evidence paths differ, use the repo-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T09:30:00Z",
  "repository": {
    "name": "visual-pushing-grasping",
    "remote_url": "https://github.com/andyzeng/visual-pushing-grasping.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "580e2334beec0d83b49e6ca89d7542b79d1d4350",
    "working_tree": "dirty-after-generation",
    "dirty_paths": ["skills/"],
    "source_dirty_note": "The pinned source tree was clean before the generated skill and review artifacts were written; skills/ is production output and is not source evidence."
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["utils", "logger", "models", "trainer", "robot", "main"]
    }
  ],
  "evidence": {
    "source_roots": ["main.py", "models.py", "trainer.py", "utils.py", "robot.py", "logger.py", "real", "simulation"],
    "docs": ["README.md", "LICENSE"],
    "examples": ["create.py", "calibrate.py", "debug.py", "touch.py", "downloads/download-weights.sh"],
    "tests": ["simulation/test-cases"],
    "configs": ["simulation/simulation.ttt", "realsense/CMakeLists.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `580e2334beec0d83b49e6ca89d7542b79d1d4350`, treat this graph as potentially stale.
- If source files, README workflow contracts, simulation preset schema,
  RealSense protocol, or public CLI flags changed, refresh the graph even when
  the commit is unchanged.
- If the current dirty paths contain source changes rather than only generated
  `skills/` output, refresh before trusting implementation-level claims.
- The pinned source is a historical Python 2/early Python 3 project with no
  distribution metadata. A successful import of the bundled offline helpers is
  not evidence that a modern full training, simulator, camera, or robot loop is
  compatible.
