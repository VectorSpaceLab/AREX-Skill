# Repository Provenance

## Purpose

Read this before deciding whether this OpenLLM skill is current for a checkout. If the current commit, package metadata, public CLI entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T15:46:24Z",
  "repository": {
    "name": "OpenLLM",
    "remote_url": "https://github.com/bentoml/OpenLLM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ec2355ce1a75176164c451cbb7592b3046531540",
    "working_tree": "clean at source-evidence capture before generated skill files were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "openllm",
      "version": "0.0.0.post1+gec2355ce1",
      "import_names": ["openllm"]
    }
  ],
  "evidence": {
    "source_roots": ["src/openllm"],
    "docs": ["README.md", "DEVELOPMENT.md"],
    "examples": [],
    "tests": [],
    "configs": ["pyproject.toml", "uv.lock"],
    "source_scripts_evidence_only": ["gen_readme.py", "release.sh"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public CLI entry points, command names, command options, package dependencies, or source modules under `src/openllm` changed, refresh the skill even if the commit is close.
- If the current checkout has docs/examples/tests that are not listed above, refresh or extend the skill so future agents can use that new evidence.
- If package version metadata no longer reports `openllm` near `0.0.0.post1+gec2355ce1`, verify that command semantics still match this skill.
