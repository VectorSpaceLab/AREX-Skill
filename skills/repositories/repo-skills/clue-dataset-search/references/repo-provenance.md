# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
CLUEDatasetSearch. If the current repo commit, dirty state, table schema, or
major evidence paths differ from this snapshot, run a repo-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:13:37Z",
  "repository": {
    "name": "CLUEDatasetSearch",
    "remote_url": "https://github.com/CLUEbenchmark/CLUEDatasetSearch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "e31458f8f25e63425da46656e0974beff5dfe437",
    "working_tree": "dirty-generated-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [],
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md",
      "NER/README.md",
      "QA/README.md",
      "情感分析/README.md",
      "文本分类/README.md",
      "文本匹配/README.md",
      "文本摘要/README.md",
      "机器翻译/README.md",
      "知识图谱/README.md",
      "语料库/README.md",
      "阅读理解/README.md"
    ],
    "scripts": [
      "scripts/file_process.sh",
      "scripts/pytmp.py",
      "scripts/t.py",
      "scripts/test.md",
      "scripts/tt.md"
    ],
    "tests": [],
    "configs": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as
  potentially stale.
- If the category README files, table columns, or maintainer scripts change,
  rebuild `references/dataset-index.json` and rerun verification.
- If the repository becomes an installable package or adds real dataset files,
  refresh the skill because the current graph intentionally covers catalogue
  metadata only.
- Ignore generated `skills/` output when deciding whether source catalogue
  evidence changed, but refresh if new source documentation or categories are
  added outside `skills/`.
