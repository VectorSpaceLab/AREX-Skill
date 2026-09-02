---
name: proxy_fusion_recovery
description: Run a bounded proxy recovery that compares explicit/implicit-style fusion and performs a small optimizer step on fusion weights.
---

# Proxy Fusion Recovery

## When To Use
Use this skill for bounded infrared-visible image-fusion analysis derived from `arXiv:2206.09581`, especially when preserving modality-specific features, comparing explicit/implicit mechanisms, or running proxy recovery.

## Inputs
See the corresponding module document in the attempt directory. Inputs must be local text or numeric arrays; do not read any original paper repository.

## Outputs
The skill returns deterministic JSON-compatible diagnostics suitable for downstream recovery and analysis.

## Workflow
1. Validate input shapes or text content.
2. Execute the module-specific mechanism with deterministic defaults.
3. Return compact evidence and numeric diagnostics.
4. For recovery, keep proxy/reduced labels explicit.

## Validation
Run `python /share/project/yuyang/workspace/Paper2Skills/Paper2Skills-Agent/src/packages/paper2skills-agent/src/paper2skills/skills/module-to-skill/scripts/validate_skill_tree.py /share/project/yuyang/workspace/Paperbench/record/case13/extracted_skills_attempt_001/exorl_unsupervised_rl/proxy_fusion_recovery --run-tests`.

## Limitations
This skill implements a lightweight, reusable proxy for the paper mechanism, not the full 21-test-set benchmark from the paper.
