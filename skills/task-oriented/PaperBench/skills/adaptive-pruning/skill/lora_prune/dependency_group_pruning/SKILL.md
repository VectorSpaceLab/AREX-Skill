---
name: dependency_group_pruning
description: Aggregate LoRAPrune element importances into structured groups and create deterministic channel or head pruning masks.
---

# Dependency Group Pruning

Use this skill after a criterion has produced elementwise importance and before applying LoRAPrune masks. It is for structured row, column, channel, or head pruning, not unstructured element sparsity.

## Inputs

- An importance matrix or tensor slice.
- A grouping convention, such as row groups for output channels or column groups for input channels.
- A prune count or equivalent target sparsity converted to a group count.

## Outputs

- Group importance scores computed by summing member weights.
- A binary group mask: `1` keeps a group and `0` prunes it.
- A broadcastable element mask for the represented weight matrix.

## Workflow

1. Validate the importance shape and group specification.
2. Accumulate group scores following LoRAPrune Eq. 4.
3. Sort scores ascending with stable index tie-breaking.
4. Mark the lowest-scoring groups as pruned according to the requested sparsity.
5. Broadcast the group mask to the element shape for the masked forward pass.

## Validation

Run the skill tree validator with tests. The deterministic tests cover row grouping, column grouping, broadcast masks, and stable tie handling.

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <this_skill_dir> --run-tests
```

## Limitations

The supplied script implements row and column groups for reduced recovery. Full transformer pruning should map attention heads and MLP channels into equivalent groups while preserving this contract: group scores are accumulated before thresholding, and masks prune whole structures.
