# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T17:24:32Z",
  "repository": {
    "name": "MetaGPT",
    "remote_url": "https://github.com/FoundationAgents/MetaGPT.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "11cdf466d042aece04fc6cfd13b28e1a70341b1f",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "metagpt",
      "version": "1.0.0",
      "import_names": ["metagpt"]
    }
  ],
  "evidence": {
    "package_metadata": ["setup.py", "requirements.txt", "MANIFEST.in", "pytest.ini"],
    "source_roots": ["metagpt"],
    "docs": ["README.md", "docs/install", "docs/tutorial", "docs/FAQ-EN.md", "docs/ACADEMIC_WORK.md"],
    "examples": ["examples", "examples/di", "examples/rag", "examples/aflow", "examples/spo", "examples/werewolf_game", "examples/stanford_town", "examples/android_assistant"],
    "tests": ["tests/metagpt", "tests/scripts"],
    "configs": ["config", "config/examples", "metagpt/configs"],
    "scripts": ["docs/scripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If package metadata, console entry points, CLI options, config schema, subpackage layout, or documented workflows changed, run `refresh-repo-skill` even on the same commit.
- If MetaGPT changes Python support, provider configuration, Data Interpreter APIs, RAG extras, extension CLIs, or maintainer test layout, refresh the relevant sub-skill.

## Evidence Notes

This skill was generated from repository evidence plus scoped live inspection of package metadata and CLI help. The full runtime dependency graph is broad and was not used as a public dependency for this skill. Public runtime instructions in this skill are self-contained and do not require the original checkout examples or scripts.
