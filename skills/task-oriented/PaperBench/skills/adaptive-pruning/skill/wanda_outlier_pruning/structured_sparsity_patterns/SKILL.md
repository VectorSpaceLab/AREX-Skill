---
name: structured_sparsity_patterns
description: Build deterministic N:M semi-structured pruning masks from Wanda or other importance scores.
---

# Structured Sparsity Patterns

Use this skill when a Wanda recovery or implementation needs 2:4, 4:8, or other N:M pruning masks. It operates on score matrices after activation-aware scoring has already been computed.

## Inputs
- Score matrix shaped outputs by inputs.
- `prune_n`: number of entries to prune in each group.
- `prune_m`: group width along the input-channel dimension.

## Outputs
- Boolean mask with exactly `prune_n` true values per complete group in each row.
- Metadata describing complete groups, ignored tail width, and achieved sparsity.

## Workflow
1. Validate `0 < prune_n <= prune_m`.
2. Split each row into consecutive groups of width `prune_m`.
3. In each complete group, mark the `prune_n` lowest scores for pruning with deterministic tie-breaking by column index.
4. Leave incomplete tail groups unpruned unless the caller pads them explicitly.

## Validation
Tests assert exact group counts and unpruned tail behavior.

## Limitations
The skill only creates masks. Applying them and checking model quality belongs to an evaluation skill.
