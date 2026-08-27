---
name: review-changes
description: "Review changed code, blast radius, test gaps, and PR comments with
  code-review-graph’s delta and PR workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Review Changes

Use this sub-skill when the task is to review a diff, explain risk, summarize impacted flows, or produce a GitHub PR comment from `detect-changes` output.

## Start here

1. Ask the graph for compact task context first:
   ```text
   get_minimal_context_tool(task="review changes")
   ```
2. If the change is small or low risk, use the compact review path.
3. If the change is broad or risky, expand to full review context and impact radius.
4. For PRs, render the report into a comment with the bundled script.

Read [references/review-workflows.md](references/review-workflows.md) for the exact review flow, token-efficiency rules, and when to use each tool. Read [references/troubleshooting.md](references/troubleshooting.md) when `detect-changes` misses symbols, the token-savings panel looks wrong, or markdown escaping/relative paths need checking.

## Route by task

| User task | Do this |
| --- | --- |
| "Review my last change" | Use `get_minimal_context_tool`, then `detect_changes_tool` or `get_review_context_tool` depending on risk. |
| "Review this PR" | Use `get_minimal_context_tool`, `get_review_context_tool`, `get_affected_flows_tool`, and `detect_changes_tool` with the PR base. |
| "Show blast radius" | Use `get_impact_radius_tool` or the review context workflow. |
| "Which functions lack tests?" | Use `detect_changes_tool` and inspect the test-gap section. |
| "Generate PR comment" | Feed `detect-changes` JSON to [scripts/render_pr_comment.py](scripts/render_pr_comment.py). |
| "Explain token savings" | Read the compact savings fields in `context_savings` and the render script. |

## Verified review surfaces

The package exposes structured review helpers for:

- `get_minimal_context`
- `get_review_context`
- `get_impact_radius`
- `detect_changes`
- affected-flow analysis
- token-savings metadata
- PR comment rendering and risk gating

The generated comment renderer escapes markdown control characters, relativizes runner paths, and keeps the hidden sticky marker as the first line so GitHub comments can be updated in place.

## Safe bundled helper

- Run [scripts/render_pr_comment.py](scripts/render_pr_comment.py) to render a PR comment or apply the risk gate to a saved JSON report.

## Boundaries

- For install/setup, use `install-and-setup`.
- For structural exploration, use `graph-exploration`.
- For embeddings, custom languages, registry/daemon, wiki, and eval workflows, use `integrations-and-extensions`.

## Verification anchors

Native tests that ground this route include change-analysis CLI tests, context-savings unit tests, PR comment rendering tests, and split-workflow security tests. Run them only during final verification, not during ordinary skill use.