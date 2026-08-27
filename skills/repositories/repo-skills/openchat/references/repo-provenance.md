# Repository Provenance

## Purpose

Read this before deciding whether this OpenChat skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, model registry, serving CLI, or evaluation harness differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:04:56Z",
  "repository": {
    "name": "openchat",
    "remote_url": "https://github.com/imoneoi/openchat.git",
    "vcs": "git",
    "branch": "master",
    "tag": "3.6.1",
    "commit": "47a3596168ed90d8f948f63f458948c3db98e2b8",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "ochat",
      "version": "3.6.1",
      "import_names": ["ochat"]
    }
  ],
  "evidence": {
    "source_roots": [
      "ochat/config",
      "ochat/serving",
      "ochat/evaluation",
      "ochat/models"
    ],
    "docs": [
      "README.md",
      "ochat/evaluation/README.md"
    ],
    "tests": [
      "ochat/tests/test_model_config.py"
    ],
    "configs": [
      "pyproject.toml",
      "pytest.ini"
    ],
    "reference_only": [
      "docker/serving/Dockerfile",
      "docker/serving/start.sh",
      "ochat/evaluation/conv_eval.py"
    ],
    "excluded": [
      "ochat/data",
      "ochat/training_deepspeed",
      "ochat/scripts",
      "ochat/experimental",
      ".github",
      "assets"
    ]
  }
}
```

The source evidence was captured from a clean checkout before writing this generated skill tree and review artifacts. Generated skill files are not part of the source-code freshness baseline.

## Refresh check

Run `refresh-repo-skill` when any of these are true:

- `git rev-parse HEAD` differs from the snapshot commit.
- The current branch/tag is a different release baseline.
- `pyproject.toml` changes the `ochat` dependencies, Python support, package versioning, or source packages.
- `MODEL_CONFIG_MAP` adds/removes model types, aliases, context lengths, EOT tokens, or default conditions.
- `ochat.serving.openai_api_server` changes CLI flags, request validation, API routes, logging/security behavior, or vLLM integration.
- `ochat.evaluation.run_eval`, `match_answer.py`, or `convert_to_evalplus.py` changes task families, output fields, data layout, or conversion behavior.
- Training/data-generation workflows become part of the desired scope.
