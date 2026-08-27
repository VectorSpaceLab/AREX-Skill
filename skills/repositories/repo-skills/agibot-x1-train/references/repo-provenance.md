# Repository Provenance

Read this file before using the skill against a checkout or deciding whether a
refresh is needed. The skill was distilled from a versioned public repository
snapshot and is intended to support multiple compatible checkouts.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "agibot-x1-train",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e6651b9ab843fd1b1be70c087bfb7e8b28e44ccd",
    "working_tree": "clean-at-source-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "humanoid",
      "version": "1.0.0",
      "import_names": ["humanoid", "humanoid.envs", "humanoid.algo", "humanoid.utils"]
    }
  ],
  "evidence": {
    "source_roots": ["humanoid", "humanoid/algo", "humanoid/envs", "humanoid/utils"],
    "docs": ["README.md", "README.zh_CN.md"],
    "examples": ["humanoid/scripts/train.py", "humanoid/scripts/play.py", "humanoid/scripts/export_policy_dh.py", "humanoid/scripts/export_onnx_dh.py", "humanoid/scripts/sim2sim.py"],
    "tests": [],
    "configs": ["setup.py", "humanoid/envs/x1/x1_dh_stand_config.py", "resources/robots/x1/urdf/x1.urdf", "resources/robots/x1/mjcf/xyber_x1_flat.xml", "resources/robots/x1/mjcf/robot/xyber_x1/xyber_x1_serial.xml"]
  }
}
```

## Refresh check

- If the current commit differs from the snapshot commit, treat this graph as
  potentially stale and run `refresh-repo-skill`.
- If the current checkout has changed package metadata, task registration,
  X1 configuration dimensions, DH policy architecture, exporter output paths,
  or MuJoCo XML layout, refresh the affected sub-skill before relying on it.
- If the source checkout is dirty, compare changed paths against the snapshot;
  the generated skill was based on the clean source commit above and does not
  include uncommitted local behavior.
- The source repository did not contain a native test suite or notebooks. The
  absence of tests is part of the evidence baseline, not evidence that runtime
  behavior is fully verified.
