# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of GPT2-Chinese. If the current commit, dirty state, package stack, or major evidence paths differ from this snapshot, run a refresh instead of assuming the skill is still aligned.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:52:16Z",
  "repository": {
    "name": "GPT2-Chinese",
    "remote_url": "https://github.com/Morizeyao/GPT2-Chinese.git",
    "vcs": "git",
    "branch": "old_gpt_2_chinese_before_2021_4_22",
    "tag": null,
    "commit": "9dc45aa24275944bec6ddfd132e0681d24d631ad",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "GPT2-Chinese source checkout",
      "version": null,
      "import_names": ["train", "train_single", "generate", "generate_texts", "eval", "tokenizations"]
    },
    {
      "name": "transformers",
      "version": "2.1.1",
      "import_names": ["transformers"]
    }
  ],
  "evidence": {
    "source_roots": ["train.py", "train_single.py", "generate.py", "generate_texts.py", "eval.py", "tokenizations/"],
    "docs": ["README.md", "README_EN.md"],
    "examples": ["sample/"],
    "tests": [],
    "configs": ["config/", "cache/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, refresh this skill.
- If the working tree dirty paths change materially, refresh this skill.
- If package metadata, CLI flags, or tokenizer behavior change on the same commit, refresh this skill.
