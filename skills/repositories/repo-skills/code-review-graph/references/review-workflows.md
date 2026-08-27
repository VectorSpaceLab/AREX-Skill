# Repo-Level Review Workflow Summary

For detailed review instructions, use `sub-skills/review-changes/`.

## Compact review path

```text
get_minimal_context_tool(task="review changes")
detect_changes_tool(detail_level="minimal")
```

Use this for low-risk changes where a concise summary is enough.

## Full review path

```text
get_minimal_context_tool(task="review PR")
get_review_context_tool(base="<base>")
get_affected_flows_tool(base="<base>")
detect_changes_tool(base="<base>", detail_level="standard")
```

Use this when the change has broad impact, public API changes, missing tests, or affected flows.

## CI path

Run `detect-changes` in CI, then render the result with the bundled review script in `sub-skills/review-changes/scripts/render_pr_comment.py`.

## Output expectations

A strong review includes:

- summary,
- risk level,
- impacted files/functions/flows,
- test gaps,
- recommended follow-up,
- and limitations such as stale graph or optional backend gaps.