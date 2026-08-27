# Repository Provenance

## Purpose

Read this before deciding whether the Stanford Alpaca skill is current for a repository snapshot. If the source commit, branch, dirty state, source scripts, dependency surface, licenses, or public workflow documents differ materially, run `refresh-repo-skill`.

## Snapshot

The snapshot below was captured before the generated skill and its review artifacts were written, when the source checkout was clean.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:51:00Z",
  "repository": {
    "name": "stanford_alpaca",
    "remote_url": "https://github.com/tatsu-lab/stanford_alpaca.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "761dc5bfbdeeffa89b8bff5d038781a4055f796a",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "stanford-alpaca-script-workflows",
      "version": null,
      "import_names": ["train", "generate_instruction", "utils", "weight_diff"]
    }
  ],
  "evidence": {
    "source_roots": ["train.py", "generate_instruction.py", "utils.py", "weight_diff.py"],
    "docs": ["README.md", "datasheet.md", "model_card.md"],
    "examples": [],
    "tests": [],
    "configs": ["configs/default_offload_opt_param.json"],
    "data": ["alpaca_data.json", "seed_tasks.jsonl", "prompt.txt"],
    "licenses": ["LICENSE", "DATA_LICENSE", "WEIGHT_DIFF_LICENSE"]
  }
}
```

## Refresh check

- If the current `HEAD` differs from the recorded commit, treat this operating skill as potentially stale.
- If source workflow files, requirements, the DeepSpeed config, the released data schema, the prompt template, or license files changed, refresh even when a related branch retains a similar structure.
- This repository is script-oriented and has no package metadata at the snapshot. Refresh if it gains a package layout, entry points, version metadata, or tests because the route and inspection strategy may change.
- A generated skill or artifact can make the checkout dirty after this snapshot; compare source changes separately from generated output.
