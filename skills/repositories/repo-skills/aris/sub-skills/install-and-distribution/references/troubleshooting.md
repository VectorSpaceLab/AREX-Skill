# Install Troubleshooting

## Slash Command Does Not Appear

- Check the correct host directory: `.claude/skills`, `.agents/skills`, or `.github/skills`.
- Confirm the skill directory contains `SKILL.md` or is a valid symlink to one.
- Restart the host agent after installation.
- If using Codex, confirm the skill came from the Codex mirror tree rather than the mainline tree unless the host explicitly supports mainline skills.

## New Upstream Skill Is Missing

During reconcile, new skills are not silently added unless the user chooses to add them or uses an add-new policy. Check the declined-skill file before assuming installer drift.

## Existing File Blocks Install

Treat this as a safety stop. Inspect the path, decide whether it is user-owned, a stale ARIS symlink, or a correct symlink not yet in the manifest. Use `--replace-link` or `--adopt-existing` only for the exact named skill after that decision.

## `.aris/tools` Missing

Some installed skills need helpers. If `.aris/tools` is missing, helper resolution may fall back to local `tools`, `ARIS_REPO`, a manifest pointer, or a global pointer. Use the bundled resolver to see which layer is active.

## Overlay Confusion

Codex base mirrors and reviewer overlays share skill names. Check which source tree a symlink points to. Claude/Gemini overlays are intended to override selected Codex mirror skills for independent review; do not mix them accidentally with mainline Claude Code install paths.

## MCP Server Still Not Connected

MCP configuration changes require host restart. First verify the CLI command exists, then verify the host's MCP list, then try a trivial prompt. Do not debug ARIS skill text until the server is registered and visible.
