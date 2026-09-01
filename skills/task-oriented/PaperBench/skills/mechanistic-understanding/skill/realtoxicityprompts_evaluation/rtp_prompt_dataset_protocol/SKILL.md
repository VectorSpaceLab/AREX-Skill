---
name: rtp_prompt_dataset_protocol
description: Normalize RealToxicityPrompts-style prompt records for toxic and non-toxic prompted generation evaluation.
---

# rtp_prompt_dataset_protocol

## When to use
Use this skill when preparing natural prompt records for RealToxicityPrompts-style evaluation. It validates prompt text, preserves stable identifiers, attaches numeric prompt toxicity, and assigns toxic/non_toxic groups with threshold >= 0.5. Do not use it to score generated continuations or compute final metrics. Inputs are JSON-like records; outputs are normalized prompt records. Workflow: load records, validate text and scores, choose threshold, normalize ids, and write JSONL/JSON. Validation command: python scripts/rtp_core.py --self-test.

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
