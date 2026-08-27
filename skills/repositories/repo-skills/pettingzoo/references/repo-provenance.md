# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the PettingZoo repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

The source evidence snapshot was captured before writing the generated `skills/` output. Generated DisCo files under `skills/` are not source evidence for PettingZoo behavior.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T18:22:01Z",
  "repository": {
    "name": "PettingZoo",
    "remote_url": "https://github.com/PettingZoo-Team/PettingZoo",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "39917484f8f37e6fb735fcd99f7bc43a53609df7",
    "working_tree": "clean-source-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pettingzoo",
      "version": "1.26.1",
      "import_names": ["pettingzoo"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pettingzoo/",
      "pettingzoo/utils/",
      "pettingzoo/test/",
      "pettingzoo/atari/",
      "pettingzoo/butterfly/",
      "pettingzoo/classic/",
      "pettingzoo/sisl/"
    ],
    "docs": [
      "README.md",
      "docs/content/basic_usage.md",
      "docs/content/environment_creation.md",
      "docs/content/environment_tests.md",
      "docs/api/",
      "docs/environments/",
      "docs/tutorials/"
    ],
    "examples": [
      "docs/code_examples/",
      "tutorials/CustomEnvironment/",
      "tutorials/CleanRL/",
      "tutorials/Tianshou/",
      "tutorials/SB3/",
      "tutorials/Ray/",
      "tutorials/AgileRL/",
      "tutorials/LangChain/"
    ],
    "tests": [
      "test/",
      "pettingzoo/test/"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "MANIFEST.in",
      "docs/requirements.txt",
      "tutorials/*/requirements.txt"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public environment modules, test helper signatures, optional dependency groups, or docs/tutorial workflows changed, run `refresh-repo-skill`.
- If a checkout is dirty only because it contains this generated `skills/` directory, compare source paths outside generated DisCo output before deciding that PettingZoo behavior changed.
- If PettingZoo adds, removes, or renames environment families, extras, wrappers, or compliance helpers, refresh the skill even on the same commit.
