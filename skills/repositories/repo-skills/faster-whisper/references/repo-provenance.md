# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T15:47:33Z",
  "repository": {
    "name": "faster-whisper",
    "remote_url": "https://github.com/SYSTRAN/faster-whisper.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ed9a06cd89a93e47838f564998a6c09b655d7f43",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "faster-whisper",
      "version": "1.2.1",
      "import_names": ["faster_whisper"]
    }
  ],
  "evidence": {
    "source_roots": ["faster_whisper/"],
    "docs": ["README.md"],
    "examples": ["docker/infer.py"],
    "tests": ["tests/test_transcribe.py", "tests/test_utils.py", "tests/test_tokenizer.py", "tests/data/"],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "requirements.conversion.txt", "MANIFEST.in", ".github/workflows/ci.yml"],
    "excluded_or_reference_only": ["benchmark/", "docker/Dockerfile", "skills/faster-whisper.log"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ in source, metadata,
  tests, or documentation paths, run `refresh-repo-skill`.
- If package metadata, public exports, `WhisperModel` or
  `BatchedInferencePipeline` signatures, model aliases, runtime dependencies,
  or source examples changed even on the same commit, run `refresh-repo-skill`.
