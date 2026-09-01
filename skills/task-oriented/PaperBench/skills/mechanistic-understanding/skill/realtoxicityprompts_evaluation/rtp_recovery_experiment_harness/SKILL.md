---
name: rtp_recovery_experiment_harness
description: Run an executable bounded recovery harness that composes prompt normalization, generation, scoring, and aggregation with mechanism checks.
---

# rtp_recovery_experiment_harness

## When to use
Use this skill to run a soft-mode recovery experiment for RealToxicityPrompts when full GPT/Perspective evaluation is blocked. It composes the dataset protocol, continuation protocol, toxicity scorer, and metric aggregation; records generated-skill invocations; and writes recovery_result.json compatible outputs. It must declare proxy status and mechanism checks. Validation command: python scripts/run_recovery_proxy.py --output /tmp/rtp_recovery_result.json.

## Input contract
JSON-compatible prompt, generation, score, or runtime records as appropriate. Required identifiers must be stable strings. Toxicity thresholds default to 0.5 and scores must be bounded in [0,1].

## Output contract
JSON-compatible records or metrics preserving identifiers, counts, thresholds, generator/scorer metadata, and explicit proxy declarations when used.

## Workflow
1. Validate inputs and fail on missing required fields.
2. Apply only this module's transformation.
3. Preserve provenance and configuration fields.
4. Write deterministic outputs suitable for downstream modules and recovery validation.

## Limitations
The included offline scorer/generator is a proxy for bounded recovery and must not be reported as an exact Perspective API or GPT reproduction.
