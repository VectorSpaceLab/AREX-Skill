# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of bitsandbytes. If the current repo commit, dirty state, package version, public APIs, package metadata, docs, examples, or tests differ materially from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "bitsandbytes",
    "remote_url": "https://github.com/bitsandbytes-foundation/bitsandbytes",
    "vcs": "git",
    "branch": "agents/skill-bitsandbytes",
    "tag": "continuous-release_main",
    "commit": "435b8b33dedbcabb364463fc1e3d11f8d1c89993",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "bitsandbytes",
      "version": "0.50.0.dev0",
      "import_names": ["bitsandbytes"]
    }
  ],
  "evidence": {
    "source_roots": ["bitsandbytes/", "csrc/"],
    "docs": ["README.md", "docs/source/"],
    "examples": ["examples/", "benchmarking/"],
    "tests": ["tests/"],
    "metadata": ["pyproject.toml", "setup.py", "CMakeLists.txt", "MANIFEST.in"],
    "scripts": ["check_bnb_install.py", "install_cuda.py", "install_cuda.sh", "scripts/stale.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If package metadata, backend support, public entry points, or important API signatures changed on the same commit, run `refresh-skill-from-repo`.
- If new docs/examples/tests add public workflows not routed by this skill, refresh or extend the skill before relying on it.
- Ignore the generated `skills/` tree itself when comparing source evidence unless the task is to update this skill.
