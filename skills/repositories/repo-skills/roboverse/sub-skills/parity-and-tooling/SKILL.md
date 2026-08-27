---
name: parity-and-tooling
description: "Guides RoboVerse cross-simulator parity experiments, registration
  and environment diagnostics, rollout tooling, and safe source-script
  selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Parity and Tooling

Use this route when comparing observations, rewards, policies, or rendered
rollouts across simulators; auditing registration; choosing a conversion or
rendering diagnostic; or deciding whether a repository script can safely become
a reusable helper.

## Route

1. Read [parity-workflows.md](references/parity-workflows.md) and define the
   comparison target, aligned initial state/action/seed, selected backends,
   metric, and stopping rule before running anything.
2. Run the safe registration/environment check in `scripts/verify_registration.py`
   for import and discovery diagnostics. It does not prove simulator parity.
3. Use [script-selection.md](references/script-selection.md) to classify scripts
   as adapt, reference-only, or exclude. Do not run real-robot, credentialed,
   long-training, sweep, or destructive conversion scripts as smoke tests.
4. Report measured deltas and backend identity. Distinguish observation/reward
   agreement from closed-loop policy transfer and from visual similarity.
5. Use [troubleshooting.md](references/troubleshooting.md) for missing backends,
   mismatched state/action order, renderer failures, and misleading parity.

Parity measurements should be reproducible and honest: a clean number must not
hide that a task fell into the void or that both sides used different resets.
