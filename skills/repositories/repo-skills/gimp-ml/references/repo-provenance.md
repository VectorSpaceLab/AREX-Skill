# Repository Provenance

Read this before deciding whether this skill is current for a checkout of
GIMP-ML. If the commit, dirty state, public entry points, or major evidence
paths differ, use a refresh workflow before relying on changed behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T17:44:17Z",
  "repository": {
    "name": "GIMP-ML",
    "remote_url": "https://github.com/kritiksoman/GIMP-ML",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "f3537a15329f29dc45f95f431a9aab4a5b8651c4",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"],
    "source_dirty_note": "The source checkout was clean before generated skill and review artifacts were added."
  },
  "packages": [
    {
      "name": "GIMP-ML source collection",
      "version": null,
      "import_names": ["gimpfu plugin modules", "gimpml service modules"]
    }
  ],
  "evidence": {
    "source_roots": ["gimp-plugins/*.py", "gimp-plugins/<model-directories>", "gimpml/"],
    "docs": ["README.md", "INSTALLATION.md", "docs/HOME.md", "docs/MANUAL.md", "docs/REFERENCES.md", "docs/DEMOS.md"],
    "examples": ["docs/DEMOS.md", "gimpml/gimp2/*.py"],
    "tests": ["gimp-plugins/DeblurGANv2/test_*.py", "gimp-plugins/EnlightenGAN/lib/nn/modules/tests/"],
    "configs": ["gimp-plugins/DeblurGANv2/config/config.yaml", "gimpml/config.json", "gimpml/requirements.txt"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` and branch with the snapshot before using this
  graph for source-bound maintenance.
- A changed or newly dirty path outside generated `skills/` should trigger a
  refresh review, especially plugin entry points, model loading code,
  `gimpml/service.py`, bridge scripts, requirements, or configuration.
- This repository is not a single normal Python distribution. Re-check the
  target host's GIMP/Python-Fu generation, model asset provenance, and service
  dependencies independently; modern service-core package availability is not
  a guarantee for every legacy plugin.
