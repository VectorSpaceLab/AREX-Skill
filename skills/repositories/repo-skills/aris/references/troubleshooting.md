# ARIS Troubleshooting

## Skill Is Not Found

1. Check the host platform's expected skill directory: `.claude/skills`, `.agents/skills`, or `.github/skills`.
2. Check the relevant manifest under `.aris/` and verify the skill name appears.
3. If the host was already running, restart it after installation or MCP configuration changes.
4. If only some skills are missing, inspect selective install choices and declined-skill files.
5. Use the official installer in `--dry-run` mode before reconciling or replacing links.

## Installer Refuses to Overwrite

This is usually correct. ARIS installers intentionally refuse to overwrite user-owned files and unexpected symlinks. Decide whether the path is user-owned or an old ARIS-managed symlink. Use a named `--replace-link` or `--adopt-existing` only when you have verified the exact entry and target.

## Helper Script Cannot Be Found

Run the bundled resolver:

```bash
python scripts/aris_helper_resolver.py --project /path/to/project --helper research_wiki.py
```

If no helper is found, repair the project-local install, set `ARIS_REPO`, or ensure the install manifest/global pointer records the ARIS checkout. Do not hardcode a local absolute path in a skill.

## Reviewer MCP Is Not Connected

- After registering or modifying MCP servers, restart the host agent.
- For Codex MCP, verify Codex CLI is installed and authenticated before registering it as an MCP server.
- For generic LLM, MiniMax, Gemini, Claude, or ModelScope routes, confirm the expected environment variables and model names.
- Missing API keys should produce explicit tool errors; do not treat them as model disagreement or research failure.
- Same-family review is provisional, not independent acceptance.

## Optional Backend Is Missing

ARIS has many optional backends: LaTeX, `pdfinfo`, GPU/SSH/Vast/Modal, Overleaf, Gemini CLI/API, MiniMax, Feishu/Lark, Codex image bridge, and OpenAI-compatible API endpoints. Missing optional backends should narrow the workflow or switch to an alternative. Do not claim a backend is verified from documentation alone.

## Research State Is Lost or Inconsistent

1. Read the latest pipeline status and fixed-name handoff artifacts.
2. Check `research-wiki/log.md` and `research-wiki/query_pack.md` if the project uses Research Wiki.
3. Check `REVIEW_STATE.json` before resuming `/auto-review-loop`.
4. Inspect `.aris/traces/` when a reviewer verdict is disputed.
5. Reconstruct the next action from files, not from memory.

## Watchdog or Experiment Status Looks Wrong

- Confirm task JSON includes `name`, `type`, `session`, and `session_type` where needed.
- Training tasks need a live `screen` or `tmux` session name and optional GPU list.
- Download tasks need a target path whose size/mtime can change.
- A missing `nvidia-smi` means GPU utilization cannot be observed; use session/file liveness instead.

## Repository Tests Fail

Route to `sub-skills/repository-maintenance/SKILL.md`. Run the smallest test file for the changed area first. Installer tests use temporary projects; MCP and provider tests mostly mock credentials and should not require live APIs unless explicitly marked integration-only.
