# Repository Provenance

Read this before deciding whether the LeRobot skill matches a checkout. If the
commit, dirty state, package version, public entry points, or major evidence
paths differ, run a refresh workflow before relying on version-sensitive
instructions.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T00:00:00Z",
  "repository": {
    "name": "lerobot",
    "remote_url": "https://github.com/huggingface/lerobot.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7427f31801f944f5ec9ce53cda02862ce7d1638b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "lerobot",
      "version": "0.6.2",
      "import_names": ["lerobot"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/lerobot",
      "src/lerobot/configs",
      "src/lerobot/datasets",
      "src/lerobot/policies",
      "src/lerobot/processor",
      "src/lerobot/envs",
      "src/lerobot/rl",
      "src/lerobot/robots",
      "src/lerobot/motors",
      "src/lerobot/cameras",
      "src/lerobot/teleoperators",
      "src/lerobot/async_inference",
      "src/lerobot/annotations",
      "src/lerobot/jobs",
      "src/lerobot/transport"
    ],
    "docs": ["README.md", "AGENT_GUIDE.md", "docs/source"],
    "examples": ["examples/dataset", "examples/training", "examples/backward_compatibility", "examples"],
    "tests": ["tests/configs", "tests/datasets", "tests/processor", "tests/policies", "tests/envs", "tests/rl", "tests/robots", "tests/motors", "tests/cameras", "tests/teleoperators", "tests/async_inference", "tests/annotations", "tests/jobs", "tests/transport"],
    "configs": ["pyproject.toml", "src/lerobot/configs", "src/lerobot/envs/metaworld_config.json"]
  },
  "public_entry_points": [
    "lerobot-info",
    "lerobot-train",
    "lerobot-eval",
    "lerobot-rollout",
    "lerobot-record",
    "lerobot-replay",
    "lerobot-calibrate",
    "lerobot-teleoperate",
    "lerobot-dataset-viz",
    "lerobot-edit-dataset",
    "lerobot-convert-dcp",
    "lerobot-annotate"
  ]
}
```

## Refresh check

- Compare the current `git rev-parse HEAD` with the snapshot commit.
- Compare branch/tag and working-tree state; this skill was generated from a
  clean `main` checkout.
- Compare `pyproject.toml` version, `project.scripts`, optional extras, and
  the source roots above.
- Re-check dataset/policy/environment/hardware APIs when a relevant module or
  CLI changes. Do not infer that a patch release preserves every optional
  backend or policy contract.

The remote URL is public provenance; private environment and checkout details
are intentionally omitted from this runtime file.
