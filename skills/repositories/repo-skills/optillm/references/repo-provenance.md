# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OptiLLM checkout. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:16:44Z",
  "repository": {
    "name": "optillm",
    "remote_url": "https://github.com/algorithmicsuperintelligence/optillm.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "eaf171aa6da5682ba1014ef342556f40247f5b35",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": [
      "skills/"
    ],
    "source_evidence_state": "clean before generated skill artifacts were written"
  },
  "packages": [
    {
      "name": "optillm",
      "version": "0.3.22",
      "import_names": ["optillm"]
    }
  ],
  "evidence": {
    "source_roots": [
      "optillm/",
      "optillm/plugins/",
      "optillm/cepo/",
      "optillm/mars/",
      "optillm/autothink/",
      "optillm/deepconf/",
      "optillm/utils/"
    ],
    "docs": [
      "README.md",
      "SSL_CONFIGURATION.md",
      "CLAUDE.md",
      "optillm/cepo/README.md",
      "optillm/mars/README.md",
      "optillm/autothink/README.md",
      "optillm/deepconf/README.md",
      "optillm/plugins/proxy/README.md",
      "optillm/plugins/spl/README.md",
      "optillm/plugins/longcepo/README.md",
      "tests/README.md"
    ],
    "tests": [
      "tests/test_approaches.py",
      "tests/test_plugins.py",
      "tests/test_mcp_plugin.py",
      "tests/test_ssl_config.py",
      "tests/test_batching.py",
      "tests/test_reasoning_simple.py",
      "tests/test_reasoning_tokens.py",
      "tests/test_json_plugin.py",
      "tests/test_compact_plugin.py"
    ],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      "requirements_proxy_only.txt",
      "optillm/cepo/configs/cepo_config.yaml",
      "optillm/cepo/configs/cepo_config_qwen3.yaml",
      "optillm/cepo/configs/cepo_config_gptoss.yaml",
      "optillm/plugins/proxy/example_config.yaml",
      "Dockerfile",
      "Dockerfile.proxy_only",
      "Dockerfile.offline",
      "docker-compose.yaml"
    ],
    "scripts": [
      "scripts/eval_aime_benchmark.py",
      "scripts/eval_arena_hard_auto_rtc.py",
      "scripts/eval_frames_benchmark.py",
      "scripts/eval_imo25_benchmark.py",
      "scripts/eval_imobench_answer.py",
      "scripts/eval_imobench_proof.py",
      "scripts/eval_math500_benchmark.py",
      "scripts/eval_optillmbench.py",
      "scripts/eval_simpleqa_benchmark.py",
      "scripts/gen_optillm_dataset.py",
      "scripts/gen_optillm_ground_truth_dataset.py",
      "scripts/gen_optillmbench.py",
      "scripts/train_optillm_classifier.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If package metadata changes from `optillm` version `0.3.22`, check whether new approaches, plugins, CLI flags, or dependencies require a refresh.
- If public files under the evidence paths above change, rerun `refresh-repo-skill` before trusting detailed API/config guidance.
- The `skills/` dirty path records this generated skill and review artifacts, not a source change used as evidence.
