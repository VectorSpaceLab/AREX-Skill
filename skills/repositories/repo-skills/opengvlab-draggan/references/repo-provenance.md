# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:45:07Z",
  "repository": {
    "name": "DragGAN",
    "remote_url": "https://github.com/OpenGVLab/DragGAN.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "69dde1546e4f0d59c55a2da0857ee17978055726",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "draggan",
      "version": "1.1.6",
      "import_names": ["draggan"]
    }
  ],
  "evidence": {
    "source_roots": ["draggan"],
    "docs": ["README.md", "INSTALL.md"],
    "examples": ["gradio_app.py", "colab.ipynb", "Dockerfile", "assets/custom"],
    "tests": [],
    "configs": ["requirements.txt", "setup.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the working tree dirty paths differ materially from this snapshot, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
