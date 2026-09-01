---
name: mapping_explanation_diagnostics
description: Diagnose visual-prompt label-mapping instability, precision, and concept-overlap explanations.
---

# Mapping Explanation Diagnostics

Use this skill after fixed FLM or ILM-VP has produced one or more target-to-source mappings. It explains whether mappings changed, stabilized, and share target/source visual attributes.

## Inputs
- Initial and final mappings or a mapping history.
- Optional descriptor dictionaries for target and source labels.
- Optional metrics for fixed and iterative runs.

## Outputs
- Changed-class count.
- Adjacent mapping stability.
- Per-pair shared attributes and explanation text.
- Accuracy/loss improvement summary.

## Workflow
1. Normalize mapping history.
2. Compare initial and final mappings.
3. Compute adjacent stability across epochs.
4. Join target/source descriptors and list shared concepts.
5. Report diagnostics separately from metric claims.

## Validation
Run `python tests/test_mapping_diagnostics.py` or `validate_skill_tree.py --run-tests`.

## Limitations
Descriptor overlap is an explanation aid, not proof of correctness. It should be combined with recovery metrics and mechanism checks.
