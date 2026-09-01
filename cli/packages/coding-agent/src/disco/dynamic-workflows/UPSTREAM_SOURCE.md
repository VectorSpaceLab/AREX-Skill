# Dynamic Workflows Upstream Provenance

This directory is an inline DisCo adaptation. It is not an npm runtime
dependency and it is not a wholesale copy of the latest upstream tree.

- Upstream repository: `https://github.com/QuintinShaw/pi-dynamic-workflows`
- Local baseline: `@quintinshaw/pi-dynamic-workflows@2.9.0`
- Local baseline commit: `452ef4ef3880a77c238f7d3ebd088b7bcad2edda`
- Reference upstream: `@quintinshaw/pi-dynamic-workflows@3.10.0`
- Reference commit: `4aaf451a97707aa7f614fc5c103ed57ae3b290c7`
- Adaptation owner: DisCo

## Implemented from the reference behavior

The current inline adaptation includes only capabilities required by the
2026-08-30 incident and its confirmed remediation scope:

- per-attempt abort signals, timeout abort/teardown before retry, default one
  timeout retry unless explicitly disabled, and no overlap between attempts;
- run-fatal sibling abort/drain so a non-recoverable environment or runtime
  failure cannot leave other lanes writing after the parent fails;
- terminal usage reconciliation, separate live usage callbacks, explicit
  estimated fallback marking, and separate cache-read/cache-write totals;
- stable workflow agent IDs and per-attempt persisted usage/error records;
- persistence of per-run limits, recovery lineage, and cumulative usage for
  resume;
- explicit `{ complete, rows, missing, errors }` coverage recognition and a
  background follow-up that instructs the main agent to recover missing IDs;
- bounded `recoverMissing()` with current-missing-only retries and explicit
  no-progress/safety-cap termination (default 50 rounds, hard cap 1000, stop
  after two consecutive rounds without shrinking the missing set);
- parser diagnostics with line, column, source excerpt, caret, and a targeted
  `args`/template-literal hint;
- structured prepared-environment executable and package/version assertions;
- bundled `workflow-authoring` guidance for safe script/args boundaries.

## Intentional DisCo adaptations retained

- `.pi` paths remain `.disco` paths;
- `subSkill`, Creator/Researcher mode, bundled resource loading, task-panel
  progress, and background result delivery remain DisCo-owned behavior;
- DisCo's `WorkflowAgent`, model routing, package/resource loader, and current
  `@earendil-works/*@0.83.0` host runtime remain in place;
- persistence remains in DisCo's project-keyed workflow store and keeps the
  existing lease mechanism;
- the existing deterministic VM and saved-workflow API remain compatible.

## Explicitly not imported in this repair

The following 3.10.0 areas were reviewed as reference but are outside this
incident-driven repair because they are not required to fix the observed
timeout, usage, partial-coverage, authoring, environment, or persistence bugs:

- full upstream workflow capability self-documentation/release-gate system;
- builtin workflow catalog changes;
- shared store and workflow-control tool;
- usage-limit scheduler;
- model-spec/routing redesign;
- extension reload and other upstream package integrations;
- any npm runtime dependency on `@quintinshaw/pi-dynamic-workflows`.

When a future synchronization changes this disposition, update this file and
add focused tests for the retained DisCo adaptations before changing the
upstream reference.
