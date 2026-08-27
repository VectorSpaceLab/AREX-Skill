# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
LaTeX-OCR repository. If the current repo commit, dirty state, package version,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T15:47:30Z",
  "repository": {
    "name": "LaTeX-OCR",
    "remote_url": "https://github.com/lukas-blecher/LaTeX-OCR.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5c1ac929bd19a7ecf86d5fb8d94771c8969fcb80",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pix2tex",
      "version": "0.1.4",
      "import_names": ["pix2tex"]
    }
  ],
  "evidence": {
    "source_roots": ["pix2tex"],
    "docs": ["README.md", "docs/installation.md", "docs/pix2tex.rst"],
    "examples": ["notebooks/LaTeX_OCR_test.ipynb", "notebooks/LaTeX_OCR_training.ipynb"],
    "tests": [],
    "configs": ["pix2tex/model/settings/config.yaml", "pix2tex/model/settings/config-vit.yaml", "pix2tex/model/settings/debug.yaml"],
    "scripts_and_services": ["pix2tex/__main__.py", "pix2tex/cli.py", "pix2tex/api", "pix2tex/dataset", "pix2tex/train.py", "pix2tex/eval.py", "docker/api.dockerfile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the dirty paths differ, run `refresh-repo-skill`.
- If package metadata, console entry points, optional extras, model config keys,
  or public API signatures changed even on the same commit, run
  `refresh-repo-skill`.
