# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of LMDeploy. If the current repo commit, dirty state, package version, public APIs, CLI flags, docs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T16:30:00Z",
  "repository": {
    "name": "lmdeploy",
    "remote_url": "https://github.com/InternLM/lmdeploy",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d9b2613182f1f94225b33239fd8dcc8903a984ce",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source checkout was clean before DisCo created the generated skill and review artifacts under skills/."
  },
  "packages": [
    {
      "name": "lmdeploy",
      "version": "0.13.0",
      "import_names": ["lmdeploy"]
    }
  ],
  "evidence": {
    "source_roots": [
      "lmdeploy/",
      "lmdeploy/pytorch/",
      "lmdeploy/turbomind/",
      "lmdeploy/vl/",
      "lmdeploy/lite/",
      "lmdeploy/serve/",
      "src/turbomind/"
    ],
    "docs": [
      "README.md",
      "docs/en/get_started/installation.md",
      "docs/en/llm/pipeline.md",
      "docs/en/llm/api_server.md",
      "docs/en/llm/api_server_responses.md",
      "docs/en/llm/api_server_anthropic.md",
      "docs/en/llm/api_server_reasoning.md",
      "docs/en/llm/api_server_tools.md",
      "docs/en/multi_modal/",
      "docs/en/quantization/",
      "docs/en/inference/",
      "docs/en/advance/pytorch_new_model.md",
      "docs/en/faq.md"
    ],
    "examples": [
      "examples/lite/qwen3_30b_a3b_awq.py",
      "examples/lite/qwen3_30b_a3b_gptq.py"
    ],
    "tests": [
      "tests/test_lmdeploy/",
      "tests/pytorch/config/",
      "tests/pytorch/paging/"
    ],
    "scripts": [
      "scripts/test_turbomind_model.py",
      "scripts/test_vlm.py"
    ],
    "metadata": [
      "setup.py",
      "pyproject.toml",
      "requirements/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If LMDeploy package metadata, CLI entry points, `GenerationConfig`, engine config dataclasses, serving protocol models, VLM media helpers, Lite quantization CLIs, or model patching registries changed, refresh the skill even if the commit is the same.
- If source checkout files outside generated `skills/` outputs are dirty, inspect those diffs before trusting this skill.
- If docs or examples moved substantially, refresh routing and bundled references before importing into another agent.
