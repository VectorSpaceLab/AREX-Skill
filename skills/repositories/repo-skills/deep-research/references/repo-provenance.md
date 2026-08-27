# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DeepResearch. If the current repo commit, dirty state, public script interfaces, README guidance, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on exact command or field claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T10:34:46Z",
  "repository": {
    "name": "DeepResearch",
    "remote_url": "https://github.com/Alibaba-NLP/DeepResearch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f72f75d8c3eb842f2bbbab096a12206ff66e270f",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "DeepResearch script collection",
      "version": null,
      "import_names": []
    },
    {
      "name": "Tongyi-DeepResearch-30B-A3B",
      "version": null,
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": [
      "inference",
      "evaluation",
      "WebAgent/WebResummer/src",
      "WebAgent/WebSailor/src",
      "WebAgent/WebWalker/src",
      "WebAgent/WebWeaver",
      "WebAgent/NestBrowse",
      "WebAgent/AgentFold",
      "WebAgent/ParallelMuse"
    ],
    "docs": [
      "README.md",
      "FAQ.md",
      "WebAgent/README.md",
      "WebAgent/WebDancer/readme.md",
      "WebAgent/WebSailor/README.md",
      "WebAgent/WebSailor-V2/README.md",
      "WebAgent/WebShaper/readme.md",
      "WebAgent/WebWatcher/README.md",
      "WebAgent/WebResearcher/README.md",
      "WebAgent/WebResummer/README.md",
      "WebAgent/WebWeaver/README.md",
      "WebAgent/WebWalker/README.md",
      "WebAgent/WebWalker/src/README.md",
      "WebAgent/WebLeaper/README.md",
      "Agent/AgentFounder/README.md",
      "Agent/AgentScaler/README.md"
    ],
    "examples": [
      "inference/eval_data/example.jsonl",
      "inference/eval_data/example_with_file.jsonl",
      "inference/eval_data/file_corpus/hello.txt",
      "WebAgent/WebDancer/datasets/sample_qa.jsonl",
      "WebAgent/WebDancer/datasets/sample_traj.jsonl",
      "WebAgent/WebSailor/src/eval_data/example.jsonl",
      "WebAgent/WebWeaver/eval_data/sample.jsonl",
      "WebAgent/WebShaper/data/webshaper.500.jsonl"
    ],
    "tests": [],
    "configs": [
      ".env.example",
      "requirements.txt",
      "WebAgent/WebDancer/requirements.txt",
      "WebAgent/WebSailor/requirements.txt",
      "WebAgent/WebWalker/requirements.txt"
    ],
    "scripts": [
      "inference/run_react_infer.sh",
      "inference/run_multi_react.py",
      "inference/react_agent.py",
      "inference/tool_search.py",
      "inference/tool_visit.py",
      "inference/tool_scholar.py",
      "inference/tool_python.py",
      "inference/tool_file.py",
      "evaluation/evaluate_deepsearch_official.py",
      "evaluation/evaluate_hle_official.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If source evidence files under `README.md`, `FAQ.md`, `inference/`, `evaluation/`, `WebAgent/`, or `Agent/` changed, refresh before relying on exact command names, environment variables, fields, or model/prerequisite claims.
- If the current tree is dirty only because it contains this generated `skills/` output, that does not by itself invalidate the source snapshot. Dirty source code, docs, configs, or examples do require a refresh.
- If DeepResearch becomes an installable package with root `pyproject.toml`, `setup.py`, or public console entry points, refresh to capture distribution metadata and import names.
