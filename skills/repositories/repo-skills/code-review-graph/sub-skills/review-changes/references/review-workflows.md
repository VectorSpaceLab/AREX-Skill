# Review Workflows

## Purpose

Read this when you need to review a code change or PR with graph-backed context, test-gap awareness, or token-savings metadata.

## Recommended flow

### 1. Start with compact context

Always start with the smallest useful context:

```text
get_minimal_context_tool(task="review changes")
```

Use the result to decide whether the change is low risk or needs a deeper pass.

### 2. Choose the review depth

- **Low risk**: use `detect_changes_tool(detail_level="minimal")` and summarize the risk, affected files, and test gaps.
- **Medium/high risk**: use `detect_changes_tool(detail_level="standard")`, then expand with `get_review_context_tool` and `get_impact_radius_tool`.
- **PR review**: use the PR base branch/ref when comparing across the whole pull request.

### 3. Useful tool patterns

| Need | Tool |
| --- | --- |
| Compact summary and suggested next steps | `get_minimal_context_tool` |
| Full changed-file context + snippets | `get_review_context_tool` |
| Blast radius around changed files | `get_impact_radius_tool` |
| Risk-scored review output | `detect_changes_tool` |
| Which flows are touched | `get_affected_flows_tool` |
| Which tests cover a symbol | `query_graph_tool(pattern="tests_for", ...)` |
| Exact graph relationships | `query_graph_tool` with callers/callees/imports/inheritors |

### 4. What to report

A good review answer normally includes:

- one-line summary of the change,
- overall risk level,
- affected functions/files/flows,
- any missing tests,
- recommendations or follow-up actions,
- and any limitations in the graph evidence.

## Token-savings metadata

Some review responses include compact `context_savings` fields. Treat them as estimates, not exact model tokenization. They are useful for explaining why the graph response is cheaper than reading every changed file in full.

## GitHub Action comment flow

The public PR workflow is backed by a reusable renderer script. The script:

- consumes `detect-changes` JSON,
- escapes markdown safely,
- relativizes CI-runner paths,
- and applies a simple risk gate.

Use it when the user asks for a sticky PR comment or a pre-rendered review summary.

## When to read troubleshooting

Read [troubleshooting.md](troubleshooting.md) if:

- `detect-changes` maps zero functions,
- the rendered report leaks absolute runner paths,
- the token-savings panel looks inconsistent,
- or a split PR workflow/security expectation changed.

## Native evidence

Relevant repo tests include the change-analysis CLI tests, context-savings tests, PR comment rendering tests, and security tests for the split analysis/comment workflows.