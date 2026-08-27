# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current JARVIS checkout. If the repository revision, dirty state, or evidence paths drift, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T13:45:03Z",
  "repository": {
    "name": "JARVIS",
    "remote_url": "https://github.com/microsoft/JARVIS.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7624cf388b47334ff8a0868e7d862dde18cfda86",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "JARVIS research repository",
      "version": "2.0.4",
      "import_names": ["easytool", "taskbench", "hugginggpt.server"]
    }
  ],
  "evidence": {
    "source_roots": ["easytool", "hugginggpt", "taskbench"],
    "docs": ["README.md", "easytool/README.md", "hugginggpt/README.md", "taskbench/README.md"],
    "examples": ["hugginggpt/server/demos", "taskbench/data_huggingface", "taskbench/data_multimedia", "taskbench/data_dailylifeapis"],
    "tests": [],
    "configs": ["hugginggpt/server/configs", "hugginggpt/web/package.json", "easytool/requirements.txt", "taskbench/requirements.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, run a refresh pass.
- If the checkout acquires new dirty paths outside generated skill outputs, refresh the skill.
- If package versions, CLI options, configs, or entry points change, refresh the relevant sub-skill.

## Notes

This snapshot was captured from the source repository before relying on the generated runtime skill. The generated skill itself is self-contained and should not depend on the source checkout remaining available.
