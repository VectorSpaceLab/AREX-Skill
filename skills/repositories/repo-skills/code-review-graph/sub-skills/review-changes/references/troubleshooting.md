# Review Troubleshooting

## `detect-changes` reports no changed functions

**Symptoms**
- Output shows a risk summary but the changed-function list is empty or obviously incomplete.
- The change was made in a tracked source file, but review context looks missing.

**Likely causes**
- The graph is stale and needs `update`.
- The changed file path was not resolved the same way the graph stores it.
- The repo root used for the review does not match the graph database location.

**Recovery**
1. Run `code-review-graph update` or `code-review-graph build` if the graph is stale.
2. Re-run the review from the repository root.
3. If the diff is large, prefer `get_review_context_tool` before the final review summary.

## Token savings look wrong

**Symptoms**
- The compact `context_savings` panel claims zero or suspiciously large savings.
- The panel exists in one command but not another.

**Likely causes**
- The response did not include a real baseline, so the savings field is omitted.
- The diff was small enough that overhead dominated the estimate.
- You used a mode that intentionally emits only summary text.

**Recovery**
1. Treat savings values as estimates, not exact token counts.
2. Use the fuller review path when you need a comparable summary.
3. Compare `detect-changes --brief` versus `update --brief` only when the graph may be stale.

## Markdown comment output leaks absolute paths or unsafe characters

**Symptoms**
- The rendered PR comment shows `/home/runner/...` or other CI runner paths.
- Markdown tables break when a file or symbol contains control characters.

**Likely causes**
- The renderer was bypassed and raw JSON was pasted directly.
- A custom downstream formatter removed the escaping or path-relativization step.

**Recovery**
1. Use the bundled PR comment renderer, not a hand-written template.
2. Keep the hidden marker as the first line of the generated comment.
3. If the renderer is modified, rerun the action-render tests.

## PR review workflow split is not being respected

**Symptoms**
- A trusted commenting workflow unexpectedly checks out untrusted code.
- A pull request job tries to comment directly from a fork.

**Likely causes**
- The workflow design was changed away from the split analysis/comment pattern.
- The trusted workflow lost its source-event gating or artifact validation.

**Recovery**
1. Keep the analysis workflow unprivileged.
2. Keep the comment-posting workflow `workflow_run`-based and locked to the default branch.
3. Validate the uploaded artifact before posting.

## When to stop

Stop and ask for help when the required fix depends on repository history, a changed CI policy, or a security permission that the current session cannot authorize.