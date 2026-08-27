# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a StarVLA checkout. If the current commit, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on detailed API or workflow guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:39:22Z",
  "repository": {
    "name": "starVLA",
    "remote_url": "https://github.com/starVLA/starVLA.git",
    "vcs": "git",
    "branch": "starVLA_dev",
    "tag": null,
    "commit": "0ed0aad2c83f587714f6167ef60cf7218b786590",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "starVLA",
      "version": "1.0.1",
      "import_names": ["starVLA", "deployment"]
    }
  ],
  "evidence": {
    "source_roots": ["starVLA", "deployment"],
    "docs": ["README.md", "docs/starVLA_guideline.md", "docs/faq.md", "docs/model_zoo.md", "docs/VM4A.md", "docs/WM4A.md"],
    "examples": ["examples/modelExtensions", "examples/simBenchmarks", "examples/realRobots"],
    "tests": ["tests"],
    "configs": ["starVLA/config", "examples/*/*/train_files"],
    "existing_guidance": ["docs/agent_skills/integrate-starvla-dataset/assets/templates"]
  }
}
```

## Refresh check

- If the current Git commit differs from `0ed0aad2c83f587714f6167ef60cf7218b786590`, treat the skill as potentially stale.
- If `pyproject.toml`, framework names, training entry points, data registry discovery, deployment server contracts, or benchmark example layouts changed, refresh even if the high-level README still looks similar.
- If a checkpoint was released against a different StarVLA revision, prefer the checkpoint's release/training revision for exact reproduction and use this skill only for current-code orientation.
- Generated skill files and review artifacts created after this snapshot are not source evidence for refresh decisions.
