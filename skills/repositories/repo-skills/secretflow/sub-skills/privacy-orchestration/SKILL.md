---
name: privacy-orchestration
description: "Guides SecretFlow PSI, secure aggregation/comparison, Kuscia, TEEU
  simulation, and deployment orchestration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Privacy and orchestration

Use this sub-skill when the task depends on privacy-preserving protocols,
cluster wiring, or deployment mode selection rather than on direct model or
component APIs.

## Owns

- PSI helpers and PSI protocol choices
- secure aggregation and comparison helpers
- Kuscia request parsing and SecretFlow cluster conversion helpers
- TEEU simulation guidance and deployment flow
- debug/simulation/production/Kuscia deployment-mode decisions
- common party/device co-location and orchestration failures

## Does not own

- plain device setup and data containers — use `runtime-data`
- direct preprocessing/statistics/classical ML APIs — use `analytics`
- component CLI / export workflows — use `component-cli`

## Trigger phrases

Use this route when a user asks things like:
- how to run PSI in SecretFlow
- how to compare or aggregate data securely
- how to parse a Kuscia task config
- how to choose debug, simulation, production, or Kuscia deployment modes
- how to use TEEU in simulation mode
- why a protocol or party layout is failing

## Reading order

1. Read `references/privacy-orchestration.md` for the protocol and deployment
   map.
2. Read the root troubleshooting page when the problem is an install, backend,
   or cluster issue that is not unique to this workflow.
3. Use `scripts/kuscia_config_smoke.py` when you want a tiny config-parser check
   that does not require any external cluster.

## Workflow

1. Pick the deployment mode before picking a protocol. The runtime shape changes
   between debug, simulation, production, and Kuscia.
2. For PSI or comparison tasks, decide which party owns the result and whether
   the inputs must already be co-located.
3. For Kuscia, parse the request shape first and only then derive the SecretFlow
   cluster config.
4. For TEEU, treat the auth-manager and memory prerequisites as part of the
   workflow, not as an afterthought.

## Common decisions

- Use the simplest PSI protocol that matches the dataset size and privacy
  needs.
- Use simulation mode when the task is about code flow or basic validation and
  not about a production deployment.
- Use Kuscia when the task names task orchestration, port reuse, or production
  scheduling.
- Use TEEU simulation for educational or quick-start validation, not as a
  production security proof.

## Bundled files

- `references/privacy-orchestration.md` — PSI, deployment, Kuscia, and TEEU notes.
- `scripts/kuscia_config_smoke.py` — tiny Kuscia config parsing helper.
