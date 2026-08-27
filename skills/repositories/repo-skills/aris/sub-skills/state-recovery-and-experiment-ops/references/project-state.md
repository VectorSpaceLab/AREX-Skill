# Project State and Recovery

## Canonical State Files

- `PIPELINE_STATUS.md`: current stage, completed work, blockers, next action, and resume instructions.
- `research_contract.md`: research question, scope, non-negotiable evidence and evaluation rules.
- `IDEA_REPORT.md`, `EXPERIMENT_PLAN.md`, `EXPERIMENT_LOG.md`, `NARRATIVE_REPORT.md`: lifecycle handoffs from idea to paper.
- `REVIEW_STATE.json`: auto-review-loop state and next round.
- Audit files: experiment, result-to-claim, paper-claim, citation, integrity, and kill-argument verdicts.
- `.aris/traces/`: raw reviewer/research traces for replay and audit.
- `research-wiki/`: persistent papers, ideas, experiments, claims, graph, log and query pack.

## Recovery Priority

1. Read the latest `PIPELINE_STATUS.md` and `research_contract.md`.
2. Check for active training or download sessions before rerunning commands.
3. Read the latest fixed-name artifact and its versioned history.
4. Inspect `REVIEW_STATE.json` if a review loop was active.
5. Use `research-wiki/query_pack.md` and `log.md` to recover accumulated context.
6. Resume from the first incomplete stage; do not repeat completed expensive work without evidence.

## Hooks

Optional host hooks can restore state at session start, refresh context periodically, remind the agent before compaction, and nudge updates after code changes. Hooks are convenience automation, not a substitute for writing durable state files.

## Output Versioning

When a workflow defines a fixed latest filename and timestamped history, write the timestamped file first and then update the fixed name. Keep canonical Markdown/JSON as the source; treat HTML as a generated view.
