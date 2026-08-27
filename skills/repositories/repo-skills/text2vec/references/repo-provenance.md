# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current commit, dirty state, package metadata, entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:46:51Z",
  "repository": {
    "name": "text2vec",
    "remote_url": "https://github.com/shibing624/text2vec.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "073e29c2135bc7805202f69322beb02c358dbe7e",
    "working_tree": "clean-at-source-discovery",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "text2vec",
      "version": "1.3.8",
      "import_names": ["text2vec"],
      "console_scripts": ["text2vec"]
    }
  ],
  "evidence": {
    "source_roots": ["text2vec"],
    "package_metadata": ["setup.py", "requirements.txt", ".github/workflows/ubuntu.yml"],
    "docs": ["README.md", "README_EN.md", "docs/model_report.md", "docs/36-text-rep-examples.md", "docs/37-text-rep-model.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "data_format_fixtures": ["examples/data/STS-B", "examples/data/snli_zh_50.jsonl", "examples/data/bge_finetune_data.jsonl"],
    "existing_repo_local_skills": ["skills/text2vec.log"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, console entry points, public import names, or core APIs in `text2vec/` changed, run `refresh-repo-skill` even if the commit is the same.
- If docs/examples/tests for embeddings, similarity/search, training, evaluation, or serving changed materially, refresh the relevant sub-skill.
- Generated skill files in `skills/` are not source evidence dirty paths; they were created after the source discovery snapshot.
