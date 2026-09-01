---
name: sabe_estimator
description: Estimate overlay load and safe available bandwidth from existing delay or packet-loss measurements using M/M/1/K equations.
---

# Silent Available Bandwidth Estimator

## When To Use
Use this skill when reconstructing or testing the SD-WAN QoS optimization mechanism from the paper. It is appropriate for reduced recovery experiments, validation fixtures, and future implementations that need the paper's silent available bandwidth estimator contract. Do not use it as evidence for full NS3 reproduction by itself.

## Inputs
- Scenario JSON with `links`, `flows`, and optional `measurements`.
- Flow records include `id`, `priority`, `demand`, `allowed_links`, `delay_sla`, and `loss_sla`.
- Link records include `id` and `capacity` in Mbps.

## Outputs
- Validated scenario objects, allocation dictionaries, SABE estimates, local-search traces, or SLA metrics depending on the entry point.
- JSON artifacts suitable for `recovery_result.json` mechanism checks.

## Workflow
1. Validate the SD-WAN flow and link model before optimization.
2. Estimate safe link capacity from passive measurements with the SABE helper when measurements are available.
3. Run priority-aware allocation before evaluating SLA satisfaction.
4. Preserve trace records showing high-priority reservation and low-priority search increments.
5. Report reduced/proxy limitations explicitly when not running packet-level simulation.

## Validation
Run `python scripts/sdwan_qos.py tests/fixture_scenario.json --output /tmp/sdwan_qos_result.json` or `python -m pytest tests` from the skill directory. The included tests use deterministic fixtures and do not require the original repository.

## Limitations
The scripts implement a compact mechanism-faithful proxy rather than the full nonlinear solver or NS3 simulator. Capacity units are Mbps and packet loss is represented as a fraction.
