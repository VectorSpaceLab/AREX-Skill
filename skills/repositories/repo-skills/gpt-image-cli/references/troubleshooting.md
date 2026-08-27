# Cross-cutting Troubleshooting

Read this when the root install/import check fails, credentials are ambiguous, a real OpenAI Images API call should not be made, or a task is unclear between CLI usage, prompt-gallery work, and repository maintenance.

## Package or import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'gpt_image_cli'` | `gpt-image-cli` is not installed in the active Python environment | Install the package into the environment that will run the task, then run `python -c "import gpt_image_cli"` and `gpt-image --help`. |
| `gpt-image: command not found` | Console script is not on `PATH` or package was installed into another environment | Use the environment's Python to run `python -m gpt_image_cli.cli --help`, or reinstall/activate so `gpt-image` is on `PATH`. |
| `pip check` reports broken `openai` or `python-dotenv` requirements | Dependency mismatch in the active environment | Repair the target environment, then rerun the root `scripts/check_install.py`. Do not mutate a user-owned environment without permission. |
| Help output lacks documented flags | CLI version drift | Check the package version and refresh this skill if `pyproject.toml` or `src/gpt_image_cli/cli.py` changed. |

## Credential and API-cost failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `error: OPENAI_API_KEY not set` | No API key in process env, `./.env`, or `~/.env` | Ask the user whether to provide a key or use a host-native image tool. Do not write secrets or create `.env` automatically. |
| User wants to avoid local API-key use | An environment or dotenv file may supply a key | Respect the request; have the user unset the variable or remove/rename dotenv files for the session. Never print the key. |
| Unexpected API billing risk | Real `gpt-image` command would call OpenAI Images API | Use dry-run/preflight helpers until the user explicitly approves a live call and quality/cost settings. |
| API error/refusal from OpenAI | Prompt policy, quota, network, model, or request parameter issue | Preserve enough stderr for debugging, lower cost with `--quality low` for retries, and avoid blind repeated calls. |

## Route confusion

- If the user asks for a **command**, **flag**, **SDK mapping**, **reference image**, **mask**, **output path**, **format**, or **exit code**, read `sub-skills/cli-and-api/SKILL.md`.
- If the user asks for a **prompt**, **visual style**, **gallery category**, **diagram**, **poster**, **UI mockup**, **research figure**, or **prompt repair**, read `sub-skills/prompt-gallery/SKILL.md`.
- If the user asks to **edit this repository**, add gallery entries, update README/plugin/package metadata, or review a PR, read `sub-skills/repo-maintenance/SKILL.md`.

## Refresh and staleness

Read `references/repo-provenance.md` before trusting this skill for a changed checkout. Refresh the skill when the current commit, package version, CLI entry point, gallery index, or existing runtime skill structure differs from the provenance snapshot.

## Import/export boundary

This generated skill was produced with a no-import policy. If a future user wants live DisCo use, run the verified repo-skill importer after final verification approval. If a future user wants Codex/Claude export, use the dedicated repo-skill export workflow rather than adding target-specific files here.
