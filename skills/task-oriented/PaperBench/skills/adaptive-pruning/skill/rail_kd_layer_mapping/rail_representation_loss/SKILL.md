---
name: rail_representation_loss
description: Compute RAIL-KD layerwise and concatenated intermediate representation losses from pooled hidden states.
---

# RAIL Representation Loss

Use this skill when a distillation experiment must implement the RAIL-KD intermediate representation objective. It is appropriate after a teacher-layer mapping has selected exactly one teacher layer for each student layer. Do not use it for attention distribution matching, MiniLM relation losses, or layer-search logic.

## Inputs

- Teacher hidden states: nested numeric lists shaped `[m][tokens][teacher_dim]`.
- Student hidden states: nested numeric lists shaped `[m][tokens][student_dim]`.
- Projection matrices for teacher and student vectors.
- Variant: `layerwise` for RAIL-KDl or `concatenated` for RAIL-KDc.
- Optional layer weights for layerwise mode.

## Outputs

- Scalar intermediate loss.
- Diagnostics containing pooled vectors, normalized vectors, and per-layer distances when applicable.

## Workflow

1. Mean-pool each selected hidden-state layer across tokens.
2. Project teacher and student vectors to the same dimension.
3. L2-normalize projected vectors with a small epsilon guard.
4. For layerwise mode, compute weighted squared distances and sum them.
5. For concatenated mode, concatenate pooled vectors first, project once, normalize, then compute one squared distance.
6. Return diagnostics for recovery mechanism checks.

## Validation

Run:

```bash
python scripts/rail_loss.py --demo
python -m pytest tests
```

## Limitations

This skill uses small pure-Python numeric lists for portability. Production transformer code should pass actual tensors through equivalent pooling, projection, normalization, and distance operations while preserving the same contracts.
