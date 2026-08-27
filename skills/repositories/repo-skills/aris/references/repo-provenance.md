# Repo Provenance

Schema: `disco.repo-provenance.v1`

- Repository: `wanshuiyin/Auto-claude-code-research-in-sleep`
- Public project name: `ARIS` / `Auto Research in Sleep`
- Source commit: `90a65e218b62d5c8eec993d08e8fc59cc19965e7`
- Branch: `main`
- Exact tag: none observed at extraction time
- Package/install metadata: no top-level Python package metadata (`pyproject.toml`, `setup.py`, or `setup.cfg`) was present. The repository is a Markdown skill corpus with shell/Python tooling and optional MCP servers.
- Observed release signal: README described ARIS-Code `v0.4.24` as the current release family at extraction time.
- Generated skill id: `aris`
- Generated skill role: operating repo skill for DisCo Researcher

## Dirty State at Extraction

The source checkout had one pre-existing untracked production log under `skills/` before generation. Generated `skills/disco/aris/` and `skills/tests/aris/` artifacts were created by this repo-skill production run and are not upstream source evidence.

## Evidence Paths Used

- `README.md`, `README_CN.md`
- `AGENT_GUIDE.md`
- `CONTRIBUTING.md`
- `SETUP_GUIDE.md`, `SETUP_GUIDE_CN.md`
- `docs/SKILLS_CATALOG.md`
- `docs/CUSTOMIZATION.md`
- `docs/PROJECT_FILES_GUIDE.md`
- `docs/SESSION_RECOVERY_GUIDE.md`, `docs/WATCHDOG_GUIDE.md`
- `docs/MODEL_COMBINATIONS.md`, `docs/LLM_API_MIX_MATCH_GUIDE.md`, `docs/MANUAL_REVIEW_GUIDE.md`
- `docs/CODEX_CLAUDE_REVIEW_GUIDE.md`, `docs/CODEX_GEMINI_REVIEW_GUIDE.md`, `docs/MINIMAX_MCP_GUIDE.md`, `docs/MODELSCOPE_GUIDE.md`
- `skills/*/SKILL.md`, `skills/shared-references/`, `skills/skills-codex/`, `skills/skills-codex-claude-review/`, `skills/skills-codex-gemini-review/`
- `tools/install_aris.sh`, `tools/install_aris_codex.sh`, `tools/install_aris_copilot.sh`, `tools/skill-groups.tsv`, `tools/skill_picker.py`, `tools/research_wiki.py`, `tools/watchdog.py`, `tools/provenance.py`, and related helper scripts
- `mcp-servers/*/server.py`
- `templates/*.md`
- `tests/test_*`

## Runtime Verification Boundary

The generated skill distills ARIS operating knowledge. It does not vendor the full ARIS installer scripts, MCP server implementations, or all 82 leaf skill contracts. Optional live integrations such as provider APIs, Feishu/Lark, Overleaf, LaTeX, remote SSH, and GPU jobs must be checked in the user's environment before execution.
