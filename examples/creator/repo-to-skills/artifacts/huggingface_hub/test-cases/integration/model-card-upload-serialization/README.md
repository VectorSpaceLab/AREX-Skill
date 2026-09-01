# Cross-route model release plan

## User Persona
A model maintainer combining local artifact validation with a reviewable Hub
release, but explicitly withholding permission for remote mutation.

## Scenario Coverage
- Skill area: root integration
- Capability: local model/card/serialization validation, Hub PR planning,
  CLI/API ownership, stale-parent recovery
- Difficulty: advanced
- Prompt file: `user_request.txt`
- Expected references/scripts: root `SKILL.md`,
  `sub-skills/hosted-compute-and-integrations/references/model-integration-and-cards.md`,
  `sub-skills/hosted-compute-and-integrations/references/serialization.md`,
  `sub-skills/hub-operations/references/workflows.md`,
  `sub-skills/cli-and-automation/references/automation-workflows.md`
- Trigger expectation: the compound local-plus-release prompt should route
  local artifacts to integrations and remote planning to Hub/CLI owners.

## Expected Successful Behavior
The response should validate card metadata, shard index and keys, DDUF structure,
and local round trips first; then produce clearly marked API/CLI PR-upload
commands with a placeholder token and an explicit parent SHA, without applying
them. It should explain PR-ref verification and bounded stale-parent recovery.

## Failure Signals
Uploading automatically, loading unsafe pickle data, skipping artifact
validation, mixing CLI and Python ownership, or retrying with a stale parent
without reinspection would fail this case.
