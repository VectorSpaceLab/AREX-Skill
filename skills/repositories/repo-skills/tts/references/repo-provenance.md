# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the source commit, working-tree state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T10:41:55Z",
  "repository": {
    "name": "TTS",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "dbf1a08a0d4e47fdad6172e433eeb34bc6b13b4e",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/tts/"
    ]
  },
  "packages": [
    {
      "name": "TTS",
      "version": "0.22.0",
      "import_names": ["TTS"]
    }
  ],
  "evidence": {
    "source_roots": ["TTS"],
    "docs": ["README.md", "docs/source"],
    "examples": ["recipes", "notebooks"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements.dev.txt", "requirements.notebooks.txt", "requirements.ja.txt", "TTS/.models.json"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, run `refresh-repo-skill`.
- If the current working-tree dirty paths differ materially from this snapshot, run `refresh-repo-skill`.
- If the package version or public entry points change, run `refresh-repo-skill`.
- If this skill is used against a different checkout of Coqui TTS, compare the new checkout to this snapshot before trusting the route map.
