---
name: rtp_continuation_generation_protocol
description: Create bounded multi-continuation records per prompt for toxic degeneration evaluation with explicit generator metadata.
---

# rtp_continuation_generation_protocol

## When to use
Use this skill when an experiment needs k continuations per prompt before toxicity scoring. It supports a real generator interface or deterministic proxy generator for bounded recovery. It must emit exactly k records per prompt and metadata naming the generator. It must not decide toxicity metrics. Inputs are normalized prompts and k; outputs are generation records. Validation command: python scripts/rtp_core.py --self-test.

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
