# Local model integration and artifact safety

## User Persona
A framework developer validating local Hub integration and artifact formats
before granting any code permission to upload.

## Scenario Coverage
- Skill area: `hosted-compute-and-integrations`
- Capability: ModelHubMixin/card creation, safetensors sharding, DDUF round trip,
  malformed index/path rejection
- Difficulty: advanced
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/hosted-compute-and-integrations/SKILL.md`,
  `sub-skills/hosted-compute-and-integrations/references/model-integration-and-cards.md`,
  `sub-skills/hosted-compute-and-integrations/references/serialization.md`,
  `sub-skills/hosted-compute-and-integrations/scripts/local_integration_smoke.py`
- Trigger expectation: local model/card/serialization language should route to
  integrations rather than Hub upload or download guidance.

## Expected Successful Behavior
The response should install/use the torch extra only when needed, prefer
safetensors, validate shard indexes and aggregate keys, parse card metadata
locally, treat DDUF as constrained rather than arbitrary ZIP, reject traversal
or malformed structure before reading/writing, and keep upload outside the
local verification path.

## Failure Signals
Loading pickle by default, trusting an index without key checks, accepting
unsafe archive names, uploading automatically, or claiming a local round trip
proves Hub compatibility would fail this case.
