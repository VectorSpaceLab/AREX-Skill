# Reviewed bucket plan boundary

## User Persona
A data operator who needs a plan-only review and an integrity check before a
bucket sync can ever apply.

## Scenario Coverage
- Skill area: `downloads-and-storage`
- Capability: JSONL plan review, prefix matching, deletion gate, plan integrity
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/downloads-and-storage/references/workflows.md`, `references/troubleshooting.md`, and the CLI sibling for exact flags
- Trigger expectation: plan/apply and bucket safety should select storage first.

## Expected Successful Behavior
The response should parse and summarize every plan action, validate source and
destination types, use component-aware prefixes, reject changed or stale plans,
and treat delete operations as a separate explicit approval gate. It should not
apply the fixture.

## Failure Signals
Applying a plan during review, matching prefixes by substring, accepting an
edited plan, or silently executing deletes fails the case.
