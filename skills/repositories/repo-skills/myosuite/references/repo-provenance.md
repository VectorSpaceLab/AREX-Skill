# Repository Provenance

## Purpose

Read this before deciding whether the MyoSuite skill matches a current source
checkout. If the commit, dirty state, package version, asset submodule commits,
or major evidence paths differ, use the refresh workflow before relying on the
operating graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T09:10:00Z",
  "repository": {
    "name": "MyoSuite",
    "remote_url": "https://github.com/MyoHub/myosuite",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "94300995076b20ed6a8cfc65794c54bc997a0697",
    "working_tree": "clean-except-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "MyoSuite",
      "version": "2.12.2",
      "import_names": ["myosuite"]
    },
    {
      "name": "mujoco",
      "version": "3.6.0",
      "import_names": ["mujoco"]
    },
    {
      "name": "gymnasium",
      "version": "1.2.3",
      "import_names": ["gymnasium"]
    }
  ],
  "asset_submodules": {
    "myosuite/simhive/MPL_sim": "58dd1abc6058e0dc06e62f13a61c36adb4916815",
    "myosuite/simhive/YCB_sim": "46edd9c361061c5d81a82f2511d4fbf76fead569",
    "myosuite/simhive/furniture_sim": "c97995afb81c9e2d7325b0069f9abc9a2c74a2f0",
    "myosuite/simhive/myo_sim": "33f3ded946f55adbdcf963c99999587aadaf975f",
    "myosuite/simhive/object_sim": "87cd8dd5a11518b94fca16bc22bb04f6836c6aa7"
  },
  "evidence": {
    "source_roots": ["myosuite/"],
    "docs": ["README.md", "docs/source/install.rst", "docs/source/suite.rst", "docs/source/api/"],
    "examples": ["tutorials/", "myosuite/utils/examine_env.py", "myosuite/utils/examine_sim.py"],
    "tests": ["myosuite/tests/"],
    "configs": ["pyproject.toml", "myosuite/agents/config/"],
    "excluded": ["benchmarks/", "release/CI infrastructure", "long-running training launchers"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Check whether the package version, Gymnasium/MuJoCo bounds, registered task
  families, public CLI options, or asset submodule commits changed.
- Treat changes under `myosuite/envs/`, `myosuite/logger/`, `myosuite/utils/`,
  `myosuite/renderer/`, `myosuite/robot/`, `myosuite/agents/`, or public docs
  as possible skill-staleness signals.
- The generated `skills/` directory is the requested output and is not source
  evidence for a future refresh.
