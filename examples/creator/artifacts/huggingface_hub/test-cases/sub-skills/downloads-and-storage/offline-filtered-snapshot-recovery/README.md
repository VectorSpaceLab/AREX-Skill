# Offline filtered snapshot recovery

## User Persona
A data engineer preparing a deterministic local dataset fixture without
credentials or network access.

## Scenario Coverage
- Skill area: `downloads-and-storage`
- Capability: dry-run, filtered snapshot, cache/offline semantics, revision and
  incomplete-snapshot diagnosis
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/downloads-and-storage/SKILL.md`,
  `sub-skills/downloads-and-storage/references/api-reference.md`,
  `sub-skills/downloads-and-storage/references/workflows.md`,
  `sub-skills/downloads-and-storage/references/configuration-cache-and-storage.md`,
  `sub-skills/downloads-and-storage/references/troubleshooting.md`
- Trigger expectation: offline/cache/pattern language should select the storage
  route rather than the generic CLI or Hub mutation route.

## Expected Successful Behavior
The response should explain that dry-run may need metadata access, select
`snapshot_download` with `repo_type="dataset"`, `revision`, `allow_patterns`,
`ignore_patterns`, and an explicit cache/local destination, then use
`local_files_only=True` only after content is seeded. It should catch and name
incomplete snapshots and separate wrong revision, missing payload, and network
availability diagnoses.

## Failure Signals
Combining `force_download` and `local_files_only`, treating a tree listing as
payload content, omitting the dataset type, or claiming a network dry-run is
offline would fail this case.
