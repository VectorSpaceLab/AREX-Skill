# Workflow Routing Troubleshooting

## The Workflow Is Too Broad

Start from the narrowest useful leaf skill or select only the needed skill group. Use the full research pipeline only when the user wants lifecycle orchestration and can provide its required handoff artifacts.

## A Phase Says an Artifact Is Missing

Check the workflow map and the current project directory. Common handoffs include `IDEA_REPORT.md`, `EXPERIMENT_PLAN.md`, `EXPERIMENT_LOG.md`, `NARRATIVE_REPORT.md`, `REVIEW_STATE.json`, audit verdict files, and a `research-wiki/` directory. Do not fabricate missing results; route back to the producer phase or mark the work blocked.

## Review Result Is Accepted Too Easily

Check executor/reviewer model families and thread freshness. Same-family Codex review is not independent cross-model acceptance. Deterministic audit tools can provide process evidence, but their scope must match the claim being gated.

## Selective Install Missing a Dependency

Inspect the catalog's `requires` edge and whether the user explicitly excluded it. A skill can be installed without an excluded dependency, but the workflow may lose a default phase or fail at a hard artifact prerequisite. Make that tradeoff visible.

## HTML and Markdown Disagree

Treat Markdown/JSON as canonical. Re-render HTML from the source instead of hand-editing the generated view.
