# Repo Provenance

- Schema: `disco.repo-provenance.v1`.
- Repository: `google/agents-cli` (current checkout directory name: `agents-cli`).
- Source baseline: Git branch `main`, commit `5a306f8956cb1eeae69f9709de0e4d61b44e11e7`.
- Exact tag at baseline: `v1.3.1`.
- Installed package inspected: `google-agents-cli==1.3.1`.
- Public command inspected: `agents-cli`, version `1.3.1`.
- Working tree state at generation: dirty only because `skills/agents-cli.log` was untracked; generated skill output was intentionally written under `skills/disco/google-agents-cli/` after that snapshot.
- Remote URL: omitted-private-or-unknown.

## Evidence Paths

The generated skill distills these repository-relative evidence sources:

- `README.md`, `RELEASE_NOTES.md`, `CONTRIBUTING.md`.
- `docs/src/cli/index.md` and `docs/src/guide/*.md` for lifecycle, setup, auth, evaluation, deployment, observability, templates, and project structure.
- `src/google/agents/cli/main.py` and command modules under `src/google/agents/cli/` for CLI routing and command behavior.
- `src/google/agents/cli/scaffold/` for template generation, deployment targets, project manifest behavior, ADK app serving glue, and template test fixtures.
- `src/google/agents/cli/eval/`, `deploy/`, `publish/`, `infra/`, `setup/`, `run/`, `dev/`, and `data/` command modules for workflow boundaries.
- `src/google/agents/cli/scaffold/agents/adk/tests/eval/` for eval dataset/config examples.
- `src/google/agents/cli/scaffold/deployment_targets/*/python/tests/` for generated integration and load-test patterns.
- Existing repo-local workflow skill directories whose IDs begin with `google-agents-cli-` for compatible workflow guidance and terminology.
- Extension metadata files `.claude-plugin/plugin.json`, `plugin.json`, and `gemini-extension.json` for package/tooling context.

## Excluded Sources

- `.git/`, caches, generated outputs, and local environments.
- `skills/tests/` review artifacts (created by this workflow, not runtime evidence).
- Cloud, GitHub, and Terraform commands were not executed during skill creation because they require credentials and can create external resources.
