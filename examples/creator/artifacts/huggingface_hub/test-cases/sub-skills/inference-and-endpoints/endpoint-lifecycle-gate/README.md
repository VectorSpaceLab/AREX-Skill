# Inference Endpoint lifecycle gate

## User Persona
A platform engineer preparing a paid endpoint change who needs a reviewable
plan and state-based recovery before any remote mutation.

## Scenario Coverage
- Skill area: `inference-and-endpoints`
- Capability: hardware discovery, endpoint configuration, health/wait state,
  pause/resume/scale-to-zero/delete safety
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/inference-and-endpoints/SKILL.md`,
  `sub-skills/inference-and-endpoints/references/api-reference.md`,
  `sub-skills/inference-and-endpoints/references/workflows.md`,
  `sub-skills/inference-and-endpoints/references/troubleshooting.md`
- Trigger expectation: dedicated Endpoint lifecycle and paid-operation language
  should route here rather than to generic Hub repository operations.

## Expected Successful Behavior
The response should query hardware/quota choices first, classify create/update/
delete as paid remote mutations, use a mocked state machine, wait for running
and healthy before exposing a client, inspect failure state/logs before retry,
and require a fresh confirmation for irreversible deletion. It should keep
custom image credentials and tokens out of output.

## Failure Signals
Hard-coding hardware, treating accepted creation as healthy, blindly retrying a
paid mutation, deleting without confirmation, or conflating an Endpoint client
with a server would fail this case.
