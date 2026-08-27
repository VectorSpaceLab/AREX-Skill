# Contributor workflows

All commands below assume you are standing in the **root of the target `gptme` checkout**, unless the command explicitly says `cd webui`.

## Repository policy

Follow the repository's maintainer rules:

- **Never push directly to `master`**. Work on a branch and open a PR.
- Use branch prefixes such as `feat/`, `fix/`, `docs/`, or `refactor/`.
- Use Conventional Commits-style messages:
  - `feat:` for new behavior
  - `fix:` for bug fixes
  - `docs:` for documentation-only changes
  - `refactor:`, `test:`, or `chore:` when appropriate
- **Stage files explicitly**. Prefer `git add path/to/file` over broad staging.
- After pushing, create the PR with `gh pr create` if the task includes publication.

## Scope discipline

Keep the package small and focused:

- Core belongs in `gptme` when the feature is needed by most users or is part of the main agent loop, tools, or providers.
- Specialized integrations, experimental features, or service-specific add-ons belong in `gptme-contrib` first.
- If you are unsure, start with `gptme-contrib` and only upstream after the feature proves broadly useful.

## Maintainer command families

Use these commands from the checkout root when you need to check the repo itself:

```bash
make test              # fast Python tests; skips slow/eval by default
make test SLOW=1       # broader Python tests; use only when needed
make typecheck         # mypy over the Python source tree
make lint              # ruff + other lint checks
make docs              # full documentation build
make check-openapi     # validate the server OpenAPI spec
```

Related packaging and release-guard commands:

```bash
cd webui && npm ci && npm run build
make bundle-webui
make validate-release-package

# From the generated repo-development sub-skill directory, or by using the linked script path explicitly:
python scripts/check_python_project_health.py --root "$TARGET_GPTME_CHECKOUT"
python scripts/check_release_package_contents.py "$TARGET_GPTME_CHECKOUT"/dist/*.whl "$TARGET_GPTME_CHECKOUT"/dist/*.tar.gz
```

Notes:

- `make bundle-webui` copies the built `webui/dist/` tree into `gptme/server/webui-dist/` for packaging.
- `make validate-release-package` is the repo's normal packaging gate; the bundled helper script provides a lighter-weight local check.
- `make release` and the publish workflows are maintainer-only and credentialed; they are intentionally outside the safe operating surface of this sub-skill.

## Performance and size guardrails

`gptme` tracks startup time and code size. The `arewetiny` guidance means you should prefer minimal, surgical changes and watch for unnecessary imports or large dependencies.

Useful maintainer checks from the checkout root:

```bash
make bench-import
make bench-startup
make tiny
make metrics
```

These checks are informative, but they are not part of the default lightweight verification loop.

## PR expectations

Current PR practice is simple:

1. Keep the diff narrow.
2. Run the relevant targeted checks locally.
3. Say what you verified.
4. Include screenshots or terminal output when the change affects UX or packaging.
5. Avoid mixing unrelated cleanup with feature work.
