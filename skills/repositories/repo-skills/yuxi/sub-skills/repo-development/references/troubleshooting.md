# Troubleshooting

This reference collects the common failures that show up while maintaining the repo and the safest way to resolve them.

## Service and stack failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Service-required checks are skipped | You did not pass `--with-services` or the Compose stack is not running | Start Docker Compose manually, then rerun the helper with `--with-services`. The helper never starts or stops services for you. |
| `docker compose exec` fails immediately | The target container is not healthy or not running | Check `docker ps` and the latest logs for `api-dev`, `worker-dev`, or `web-dev`. |
| API or worker changes appear to do nothing | The live stack was never started, or the wrong files were edited | Confirm the code lives under the mounted source tree and inspect container logs instead of relying on assumptions. |
| Frontend tests or lint fail because dependencies are missing | Node modules were never installed in `web/` | Install the frontend dependencies and rerun the check. |
| Backend pytest cannot find dependencies | The backend environment is stale or the wrong directory was used | Run the command from `backend/` and use the package import smoke test to confirm the environment first. |

## Lint, format, and diff hygiene

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Frontend lint rewrites files | That is expected from the repo's maintained lint path | Use the explicit ESLint check when you only want a no-write validation step. |
| `make format` touches more files than expected | The command is intentionally broad | Review the diff, keep only the intended changes, and rerun narrower checks if needed. |
| `make lint` is not a pure check | The frontend lint script still auto-fixes | Prefer the explicit ESLint check or the bundled helper for read-only validation. |
| `git diff --check` fails | Whitespace or line-ending issues | Fix the patch before committing. |

## Version and release failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| The bump script changed more than you expected | You ran the wrong mode or picked the wrong version | Revert, choose the correct target, and rerun only after confirming the intended release mode. |
| A tag already exists | You are trying to reuse a published version | Do not force overwrite the tag; pick a new version or ask for a manual decision. |
| Docs changed but the site build fails | The new page is not wired into the VitePress nav or sidebar | Update `docs/.vitepress/config.mts` and rebuild the docs site. |

## Package and command failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Backend import smoke fails because `yuxi` imports too much | The package import contract regressed | Treat that as a real packaging issue and inspect the newly added eager import. |
| CLI pytest fails on help or command wiring | The Typer app or command registration changed | Keep the CLI tests green before touching release or publish workflow assumptions. |
| Frontend unit tests fail after a store change | The changed state contract is now inconsistent with the UI expectations | Update the affected test in `web/test/unit/` before widening the change. |

## Safety gates

- Do not print secrets or copy `.env` values into logs, docs, or tests.
- Do not start or stop Compose services from the helper script.
- Do not call external model providers, Langfuse, or non-local OCR engines unless the task explicitly needs them and the required credentials are available.
- Do not claim success for a service-required check that was never actually run.

## When to stop and ask

Stop and ask the user when:

- the task needs live services but the stack is not available,
- the version bump target is unclear,
- the change would require overwriting an existing release tag,
- or the requested validation depends on external credentials or provider access that is not configured.
