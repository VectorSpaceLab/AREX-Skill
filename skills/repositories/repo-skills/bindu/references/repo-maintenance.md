# Repo Maintenance Notes

Use these notes only when the user is modifying or validating a Bindu checkout. For using Bindu as an installed package, prefer the relevant operating sub-skill.

## Common commands

```bash
uv sync
uv run pytest tests/unit/
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy bindu
uv run pre-commit run --all-files
cd sdks/typescript && npm run build
cd inbox && npm run dev
bash scripts/generate_protos.sh all
```

## Repository gotchas

- Do not edit generated code under `bindu/grpc/generated/` or `sdks/typescript/src/generated/`. Edit the proto and regenerate.
- Use `get_logger(__name__)` from `bindu/utils/logging.py`, not `print()`, in package code.
- Use `app_settings` from `bindu/settings.py` for configuration instead of ad hoc environment reads.
- Use `dict.pop(key, None)` for optional metadata/context keys instead of `del dict[key]`.
- Never commit `.env` files. Use `.env.example` only, with the repository's secret-scan allowlist comments when needed.
- Keep PRs focused and coordinate on issues before coding when the contribution policy requires it.

## Existing agent playbooks

The checkout may include local `.agents/skills/` playbooks for tasks such as testing a PR, deployment, release creation, regenerating gRPC stubs, adding examples, or debugging gRPC connections. Treat those as maintainer workflow evidence, not runtime dependencies of this generated skill.

## Safe validation order

1. Read the task-specific sub-skill.
2. Check install/import/CLI surface.
3. Run the narrowest relevant unit tests.
4. Run integration/e2e tests only when services, credentials, and time budget are appropriate.
5. Run formatting/lint/pre-commit before proposing a PR.
