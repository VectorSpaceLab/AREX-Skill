# Card and discussion triage

## User Persona
A maintainer who knows Hub concepts but needs a careful read-first workflow
for metadata and community operations.

## Scenario Coverage
- Skill area: `hub-operations`
- Capability: local card validation, collections, discussions/PRs, safe mutation
  planning, repo-type diagnosis
- Difficulty: advanced
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/hub-operations/references/api-reference.md`,
  `sub-skills/hub-operations/references/workflows.md`,
  `sub-skills/hub-operations/references/troubleshooting.md`
- Trigger expectation: cards, collection, discussion URL, and approval gates
  should route to the Hub resource owner.

## Expected Successful Behavior
The response should parse the card locally before network access, distinguish
metadata from body text, use explicit collection/discussion identifiers and
repo type, inspect current state and events, classify commenting/PR operations
as mutations, and require exact target confirmation. It should recommend
redacted summaries instead of dumping webhook or token-bearing objects.

## Failure Signals
Treating card metadata as valid without parsing, using a bucket or plural repo
type, commenting immediately, exposing secrets, or giving only generic API
advice indicates insufficient depth.
