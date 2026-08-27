# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package/library context, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:55:55Z",
  "repository": {
    "name": "Chinese-BERT-wwm",
    "remote_url": "https://github.com/ymcui/Chinese-BERT-wwm.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4c256d460f30cf899f42a16f4125be205e9ea270",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "Chinese-BERT-wwm",
      "version": null,
      "import_names": []
    },
    {
      "name": "transformers",
      "version": "5.15.0",
      "import_names": ["transformers"]
    },
    {
      "name": "torch",
      "version": "2.13.0",
      "import_names": ["torch"]
    }
  ],
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md",
      "README_EN.md"
    ],
    "examples": [],
    "tests": [],
    "configs": [],
    "data": [
      "data/bqcorpus/README.md",
      "data/chnsenticorp/README.md",
      "data/chnsenticorp/chnsenticorp.zip",
      "data/cjrc/README.md",
      "data/cmrc2018/README.md",
      "data/drcd/README.md",
      "data/lcqmc/README.md",
      "data/msra-ner/README.md",
      "data/peopledaily/README.md",
      "data/peopledaily/peopledaily.zip",
      "data/thucnews/README.md",
      "data/weibo/README.md",
      "data/weibo/weibo.zip",
      "data/xnli/README.md"
    ],
    "excluded": [
      ".git/",
      ".github/",
      "pics/",
      "skills/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If model identifiers, dataset README pointers, or benchmark tables change, refresh this skill even if the repository remains documentation-only.
- If future repository versions add installable package code, examples, scripts, or tests, refresh this skill because its current provenance records no package source roots, examples, or tests.
- If Transformers loading semantics change materially, refresh the API reference and bundled check scripts.

## Construction Notes

This skill was generated from a documentation/data resource repository rather than an installable Python package. The verified Python package facts describe external libraries used to operate the public HFL model ids; they are not local package metadata for this repository.
