# Ambiguous upload outcome

## User Persona
An automation engineer handling a request timeout after a potentially accepted
Hub mutation.

## Scenario Coverage
- Skill area: `hub-operations`
- Capability: read-after-timeout, PR/ref inspection, duplicate prevention,
  bounded retry
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/hub-operations/references/workflows.md` and `references/troubleshooting.md`
- Trigger expectation: timeout plus upload/PR state should route to Hub
  operations, not generic HTTP retry advice.

## Expected Successful Behavior
The response should treat the outcome as ambiguous, re-read state and current
SHA, inspect existing PRs and paths, decide reuse versus one retry based on
observed state, and verify the resulting ref. It must not blindly repeat the
mutation or expose credentials.

## Failure Signals
An unconditional retry, no duplicate check, no post-check, or token in a log
would fail the case.
