# Private dataset PR conflict recovery

## User Persona
An experienced Python user automating Hub repository changes, who wants a
reviewable PR and understands optimistic concurrency but cannot use a live Hub
credential in the test.

## Scenario Coverage
- Skill area: `hub-operations`
- Capability: private dataset creation/reuse, revision inspection, PR upload,
  stale-parent recovery, token redaction
- Difficulty: troubleshooting
- Prompt file: `user_request.txt`
- Expected references/scripts: `sub-skills/hub-operations/SKILL.md`,
  `sub-skills/hub-operations/references/api-reference.md`,
  `sub-skills/hub-operations/references/workflows.md`,
  `sub-skills/hub-operations/references/troubleshooting.md`
- Trigger expectation: explicit HfApi/repository/PR/concurrency signals should
  route directly to the Hub operations owner.

## Expected Successful Behavior
The response should establish the repo type and revision, keep the token out of
logs, use `exist_ok` only for idempotent existence, capture the current parent
SHA, set `create_pr=True` and `parent_commit`, handle a stale-parent 409 by
re-reading state and checking for an existing PR, retry at most once with the
new SHA, and verify `CommitInfo.pr_revision` and the intended path.

## Failure Signals
Blindly retrying a non-idempotent upload, dropping `parent_commit`, mutating
`main` unexpectedly, creating duplicate PRs, using a plural Python repo type,
printing the sentinel token, or referring the user to original checkout tests
would fail this case.
