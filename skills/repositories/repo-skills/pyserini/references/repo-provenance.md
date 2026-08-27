# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Pyserini. If the current repo commit, dirty state, package version, Java/resource behavior, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T18:58:58Z",
  "repository": {
    "name": "pyserini",
    "remote_url": "https://github.com/castorini/pyserini",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "15aa02048027213790451d1beaa1023355fc8ff6",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pyserini",
      "version": "2.3.0",
      "import_names": ["pyserini"]
    }
  ],
  "runtime_observations": {
    "python_requires": ">=3.12",
    "java_required": "21 for Anserini/Lucene-backed workflows",
    "faiss": "optional package needed for Faiss workflows and some server import paths",
    "source_checkout_resources": "editable source checkouts may need Anserini fatjar and eval resources built or provided separately"
  },
  "evidence": {
    "metadata": ["pyproject.toml", "MANIFEST.in", "README.md", "project-description.md"],
    "source_roots": ["pyserini"],
    "docs": [
      "docs/installation.md",
      "docs/usage-index.md",
      "docs/usage-search.md",
      "docs/usage-fetch.md",
      "docs/usage-indexreader.md",
      "docs/usage-analyzer.md",
      "docs/usage-querybuilder.md",
      "docs/usage-rest.md",
      "docs/usage-mcp.md",
      "docs/reproducibility.md",
      "docs/prebuilt-indexes.md",
      "docs/release-notes"
    ],
    "examples_and_scripts": ["scripts", "bin", "integrations"],
    "tests": ["tests/base", "tests/core", "tests/optional", "tests/resources"],
    "existing_agent_guidance": [".agents/skills/install-pyserini-dev", ".agents/skills/install-pyserini-uv"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, required Python/Java versions, optional dependency declarations, server config semantics, CLI flags, public API signatures, or source resource packaging changed, run `refresh-repo-skill`.
- If the current checkout has different dirty paths beyond generated skill output, inspect whether those paths affect the evidence map before using this skill as authoritative.
- If Pyserini changes how it packages Anserini/eval resources, refresh `install-and-runtime`, `serving-and-agent-tools`, and `repo-development` together.
