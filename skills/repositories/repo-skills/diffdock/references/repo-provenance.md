# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DiffDock. If the current repo commit, dirty state, package/runtime behavior, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "DiffDock",
    "remote_url": "https://github.com/gcorso/DiffDock",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "85c49b60d3e0b0182a59ee43a34a6d7036981284",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["inference", "evaluate", "train", "confidence", "datasets", "models", "utils", "app", "spyrmsd"]
    }
  ],
  "evidence": {
    "source_roots": ["inference.py", "evaluate.py", "train.py", "confidence", "datasets", "models", "utils", "app", "spyrmsd"],
    "docs": ["README.md", "app/README.md"],
    "examples": ["examples", "data/protein_ligand_example.csv", "data/testset_csv.csv"],
    "tests": [],
    "configs": ["environment.yml", "requirements.txt", "app/requirements.txt", "default_inference_args.yaml", "Dockerfile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If the working tree has source, config, docs, app, dataset, model, or utility changes beyond generated `skills/` output, refresh this skill.
- If DiffDock gains packaging metadata, console entry points, new model defaults, new data layouts, or changed command flags, refresh this skill.
