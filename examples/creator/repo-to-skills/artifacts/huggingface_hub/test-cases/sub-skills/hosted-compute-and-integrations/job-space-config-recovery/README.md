# Hosted compute configuration recovery

## User Persona
A platform engineer preparing cloud resources who needs a no-cost, no-remote
preflight and clear status-based recovery.

## Scenario Coverage
- Skill area: `hosted-compute-and-integrations`
- Capability: Jobs/Spaces config validation, secret/variable hygiene, lifecycle
  state diagnosis, client-timeout distinction, safe termination
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/hosted-compute-and-integrations/SKILL.md`,
  `sub-skills/hosted-compute-and-integrations/references/jobs-and-sandboxes.md`,
  `sub-skills/hosted-compute-and-integrations/references/spaces-and-server-integrations.md`,
  `sub-skills/hosted-compute-and-integrations/references/troubleshooting.md`
- Trigger expectation: Jobs, Spaces, resources, secrets, and billing language
  should route to hosted compute/integrations.

## Expected Successful Behavior
The response should validate all configuration locally, keep secrets in secret
fields and out of diagnostics, model Job/Space terminal states, distinguish a
client wait timeout from server failure, require authorization before remote
mutation, and include pause/stop/cleanup guidance for billable resources.

## Failure Signals
Launching a real resource, logging secret values, treating streamed logs as
success, retrying a failed configuration blindly, or omitting termination and
billing safeguards would fail this case.
