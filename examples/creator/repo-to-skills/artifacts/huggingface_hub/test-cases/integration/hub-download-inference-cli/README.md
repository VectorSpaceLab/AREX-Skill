# Cross-route model discovery, storage, inference, and CLI rehearsal

## User Persona
An ML platform developer composing Hub discovery, artifact planning, hosted
inference, and shell automation while keeping the rehearsal hermetic.

## Scenario Coverage
- Skill area: root integration
- Capability: root routing across Hub API, storage, inference, and CLI owners;
  support-workflow and stream-boundary integration
- Difficulty: advanced
- Prompt file: `user_request.txt`
- Expected references/scripts: root `SKILL.md`,
  `sub-skills/hub-operations/references/api-reference.md`,
  `sub-skills/downloads-and-storage/references/workflows.md`,
  `sub-skills/inference-and-endpoints/scripts/mock_chat_recovery.py`,
  `sub-skills/cli-and-automation/references/automation-workflows.md`
- Trigger expectation: the compound prompt should yield distinct owners rather
  than loading or duplicating the entire graph.

## Expected Successful Behavior
The response should identify read-only model discovery, dry-run/filtered cache
planning, mocked inference, and CLI stdout/stderr parsing as separate stages.
It should preserve no-network/no-token constraints, route each stage correctly,
and verify outputs without applying a transfer or paid call.

## Failure Signals
A single unbounded remote workflow, mixed JSON/stderr parsing, a CPU/GPU claim
about hosted inference, or missing cross-links and safety classification would
fail this case.
