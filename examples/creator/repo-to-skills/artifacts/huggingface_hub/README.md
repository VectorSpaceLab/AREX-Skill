# `huggingface_hub` Creator artifacts

This bundle accompanies the sanitized Creator session in
[`../../disco-creator-huggingface_hub.html`](../../disco-creator-huggingface_hub.html).
It records the public, reviewable outputs of a task-agnostic Creator run for
`huggingface/huggingface_hub` at source commit
`4237d95c603db491cb1070898c74c97e4d7c2582` (`v1.29.0`).

## Included

- [`huggingface-hub/`](huggingface-hub/) — the generated runtime skill, with its
  root router, five focused sub-skills, references, and safe bundled helpers.
- [`review/final-skill-report.md`](review/final-skill-report.md) — scope,
  coverage, verification boundaries, and import-readiness summary.
- [`review/human-review.md`](review/human-review.md),
  [`review/prompt-sampling.md`](review/prompt-sampling.md), and
  [`review/publication-checklist.md`](review/publication-checklist.md) — human
  review and publication evidence.
- [`review/verification-report.json`](review/verification-report.json) — the
  machine-readable static and runtime verification summary.
- [`review/native-verification-report.json`](review/native-verification-report.json)
  — native-test outcomes, including explicitly reported warnings, skips, and
  environment/service-specific failures. Raw log paths are omitted.
- [`review/routing-decision.json`](review/routing-decision.json) and
  [`review/evidence.md`](review/evidence.md) — the sanitized taxonomy decision
  and its supporting evidence.
- [`review/license-resolution.json`](review/license-resolution.json) — the
  resolved `Apache-2.0` runtime license record.
- [`review/integration-notes.md`](review/integration-notes.md) — graph ownership,
  grounding, and construction decisions.
- [`test-cases/`](test-cases/) — 15 assertion-backed usability cases covering
  root routing, all five sub-skills, and two integrated compositions.

## Intentionally excluded

The public bundle does not include the original source checkout, private
environment handoff (`repo_env_report.json`), raw native logs, credentials or
tokens, caches, generated temporary state, or the original un-sanitized HTML.
The runtime skill also does not depend on the review bundle or on the source
repository checkout.

The native report preserves the meaning of each result but omits links to raw
logs that are not distributed here. The routing decision omits the original
local checkout path. Paths shown in the session and review artifacts are
portable example paths rather than workstation-specific paths.
