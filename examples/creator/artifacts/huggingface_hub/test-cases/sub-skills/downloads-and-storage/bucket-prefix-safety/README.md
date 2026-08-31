# Bucket prefix and traversal safety

## User Persona
An operator planning object-storage movement who wants to inspect a proposed
transfer without accidentally selecting similarly named prefixes or a path
outside the destination.

## Scenario Coverage
- Skill area: `downloads-and-storage`
- Capability: bucket URI interpretation, prefix boundaries, trailing slash,
  traversal rejection, plan/apply safety
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/downloads-and-storage/SKILL.md`,
  `sub-skills/downloads-and-storage/references/workflows.md`,
  `sub-skills/downloads-and-storage/references/troubleshooting.md`
- Trigger expectation: bucket/path/sync safety should route to storage planning.

## Expected Successful Behavior
The response should treat buckets as mutable object storage, inspect source and
destination kinds, explain that a trailing slash copies contents rather than the
source directory node, use a dry-run or plan, compare path components so
`logs/` does not include `logs-old/`, and reject every `..` path before applying
anything. It should route exact CLI syntax to the CLI sub-skill when needed.

## Failure Signals
Applying a remote copy, splitting an `hf://` mount naively, matching prefixes
by substring, accepting traversal, or treating HfFileSystem read APIs as a
safe authorization boundary would fail this case.
