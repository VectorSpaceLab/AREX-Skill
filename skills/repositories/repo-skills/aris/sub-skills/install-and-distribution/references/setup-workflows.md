# Setup Workflows

## Claude Code / Cursor / Trae / Antigravity

Expected project layout after install:

```text
<project>/
  CLAUDE.md
  .claude/skills/<skill-name> -> <aris-repo>/skills/<skill-name>
  .aris/installed-skills.txt
  .aris/tools -> <aris-repo>/tools
```

Typical sequence:

1. Ensure the host agent CLI is installed.
2. Ensure Codex CLI is installed and authenticated when ARIS will use Codex MCP as reviewer.
3. Register Codex MCP under the expected server name, then restart the host agent.
4. In each research project, run the official ARIS installer from the user's ARIS checkout.
5. Verify a small skill invocation and the `.aris/tools` helper path.

## Codex CLI

Expected layout:

```text
<project>/
  AGENTS.md
  .agents/skills/<skill-name> -> <aris-repo>/skills/skills-codex/<skill-name>
  .aris/installed-skills-codex.txt
```

Codex base mirrors use Codex-native review. That review can complete workflows but is same-family by default and should be marked provisional unless an independent reviewer overlay or deterministic verifier accepts it.

Optional overlays:

- Claude-review overlay: install when Codex is executor and Claude is reviewer.
- Gemini-review overlay: install when Codex is executor and Gemini is reviewer.

## GitHub Copilot CLI

Expected layout:

```text
<project>/
  .github/skills/<skill-name> -> <aris-repo>/skills/<skill-name>
  .aris/installed-skills-copilot.txt
```

Copilot uses mainline `SKILL.md` semantics directly. Its `/auto-review-loop` can use host-proven complementary reviewer evidence when available; preserve the same-family/provisional distinction.

## Selective Install

The catalog uses tab-separated group and skill records. Groups cover literature, ideation, review loops, theory, experiments, paper core, visuals, submission, patents, and meta utilities. For a small setup:

- Use `--list-groups` to inspect groups.
- Use `--groups` for a role-oriented install.
- Use `--skills` for precise skills and their cataloged hard dependencies.
- Use `--exclude` to prevent a dependency from being auto-included; expect a warning if the excluded skill is normally required.

## Post-Install Verification

- Confirm the host skill root contains symlinks or skill directories.
- Confirm the matching `.aris/installed-skills*.txt` manifest exists.
- Confirm `.aris/tools` exists for Claude/mainline installs that need helpers.
- Confirm the host recognizes a simple ARIS skill after restart.
- If Research Wiki is selected, initialize it once in the project before expecting other skills to read it.
