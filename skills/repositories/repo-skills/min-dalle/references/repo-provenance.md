# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:41:31Z",
  "repository": {
    "name": "min-dalle",
    "remote_url": "https://github.com/kuprel/min-dalle.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "73621fb280b42f1b3aa05786447ddfbf09dada33",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "min-dalle",
      "version": "0.4.11",
      "import_names": ["min_dalle"]
    }
  ],
  "evidence": {
    "source_roots": ["min_dalle/", "min_dalle/models/"],
    "docs": ["README.md", "min_dalle.ipynb"],
    "examples": ["examples/", "image_from_text.py", "tkinter_ui.py"],
    "tests": [],
    "configs": ["setup.py", "requirements.txt", "replicate/cog.yaml"],
    "deployment": ["replicate/predictor.py"],
    "license": ["LICENSE"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from the snapshot, especially outside generated `skills/` artifacts, run `refresh-repo-skill`.
- If `setup.py`, package dependencies, public imports, `MinDalle` signatures, model asset filenames, or interface scripts change, run `refresh-repo-skill` even on the same commit.
- If a future version adds tests, console entry points, extra packages, new deployment configs, or changes model-host URLs, refresh before relying on this skill.
