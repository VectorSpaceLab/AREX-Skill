# CLI stdout/stderr and delete gate

## User Persona
A scripting-oriented user who needs machine-readable CLI output without losing
warnings and wants destructive commands to fail closed.

## Scenario Coverage
- Skill area: `cli-and-automation`
- Capability: version/help discovery, JSON dry-run parsing, stderr separation,
  confirmation refusal
- Difficulty: intermediate
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/cli-and-automation/SKILL.md`,
  `sub-skills/cli-and-automation/references/cli-reference.md`,
  `sub-skills/cli-and-automation/references/automation-workflows.md`,
  `sub-skills/cli-and-automation/scripts/check_cli_help.py`
- Trigger expectation: command, flags, JSON, stderr, and confirmation language
  should select the CLI owner.

## Expected Successful Behavior
The response should run `hf version` and command help first, parse stdout only,
keep stderr separately, use dry-run before a transfer, and demonstrate that a
repository delete without `--yes` exits non-zero before an API call. It should
show placeholders and use a fake fixture rather than real network or tokens.

## Failure Signals
Parsing combined streams as JSON, adding `--yes` to bypass review, invoking a
real placeholder repo, or trusting a stale command catalog without live help
would fail this case.
