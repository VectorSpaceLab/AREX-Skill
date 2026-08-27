# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of LiteLLM. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T06:41:29Z",
  "repository": {
    "name": "litellm",
    "remote_url": "https://github.com/BerriAI/litellm",
    "vcs": "git",
    "branch": "litellm_internal_staging",
    "tag": null,
    "commit": "84c1414aef6732254d7ec17c544b6b77cb90d460",
    "dirty_state": ["?? skills/"]
  },
  "package": {
    "distribution": "litellm",
    "import_name": "litellm",
    "version": "1.90.0",
    "python_requires": ">=3.10,<3.14"
  },
  "evidence_paths": [
    "pyproject.toml",
    "README.md",
    "litellm/",
    "litellm/proxy/",
    "litellm/llms/",
    "litellm/router.py",
    "litellm/router_strategy/",
    "litellm/router_utils/",
    "litellm/caching/",
    "litellm/integrations/",
    "litellm/a2a_protocol/",
    "litellm/experimental_mcp_client/",
    "litellm-proxy-extras/",
    "enterprise/",
    "cookbook/",
    "scripts/",
    "tests/router_unit_tests/",
    "tests/proxy_unit_tests/",
    "tests/proxy_behavior/",
    "tests/mcp_tests/",
    "tests/pass_through_unit_tests/",
    "tests/llm_responses_api_testing/",
    "tests/guardrails_tests/"
  ],
  "excluded_or_deprioritized_paths": [
    "ui/",
    "deploy/",
    "docker/",
    "helm/",
    "terraform/",
    ".github/",
    ".circleci/",
    "dist/",
    "build/",
    "benchmarks and load tests",
    "credential-bearing fixtures"
  ]
}
```

## Notes

The dirty state may include the generated `skills/` output from this DisCo run. Treat source-code changes outside generated skill artifacts as stronger staleness signals than the generated artifacts themselves.
