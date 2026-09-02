---
name: rtp_toxicity_scoring_adapter
description: Attach numeric toxicity scores to generated continuations using Perspective API or declared offline proxy scoring.
---

# rtp_toxicity_scoring_adapter

## When to use
Use this skill to convert generated continuation text into toxicity scores in [0,1]. In full recovery this wraps Perspective API or another detector; in soft bounded recovery it may use the included lexicon proxy if declared. It preserves prompt and continuation identifiers. It does not aggregate prompt groups. Validation command: python scripts/rtp_core.py --self-test.

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
