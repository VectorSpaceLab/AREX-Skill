# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the ModelScope repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:57:23Z",
  "repository": {
    "name": "modelscope",
    "remote_url": "https://github.com/modelscope/modelscope.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f0592cb67ee5bbb16ea0e31c3274ed34d8504d34",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "modelscope",
      "version": "2.0.0+main",
      "import_names": ["modelscope"]
    },
    {
      "name": "modelscope-hub",
      "version": "0.2.0",
      "import_names": ["modelscope_hub"]
    }
  ],
  "evidence": {
    "source_roots": ["modelscope"],
    "docs": ["README.md", "README_zh.md", "README_ja.md", "docs/source/command.md", "docs/source/server.md", "docs/source/develop.md", "docs/source/api"],
    "examples": ["examples/pytorch", "examples/apps"],
    "tests": ["tests/cli", "tests/fileio", "tests/msdatasets", "tests/pipelines", "tests/trainers", "tests/export", "tests/models"],
    "configs": ["configs", "requirements", "pyproject.toml", "setup.cfg", "setup.py", "MANIFEST.in"],
    "tools": ["modelscope/tools", "tools", "modelscope/server", "modelscope/exporters"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If package metadata, console scripts, optional dependency groups, or public API signatures changed, refresh even on the same branch.
- If `modelscope_hub` CLI command help changes materially, refresh the Hub/CLI sub-skill or record the target-version difference in task notes.
- If a task requires full CUDA, vLLM, TensorFlow, audio, CV, NLP, multi-modal, or science model execution, verify that backend in the target environment; this provenance only records package-level CPU/base verification.
