---
name: taxonomy_recovery_harness
description: Run a reduced executable WordNet taxonomy recovery using generated preprocessing, tagging, and distance skills.
---

# Taxonomy Recovery Harness

Use this skill after the WordNet taxonomy module skills have been generated and validated. It coordinates the reduced soft-mode recovery and writes validator-compatible experiment artifacts.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing the taxonomy, preprocessor, tagger, and distance skills.

## Outputs
- `recovery/recovery_result.json` with numeric proxy metrics.
- `recovery/logs/generated_data_item.json` describing the reduced sample.
- `recovery/logs/training_trace.json` with loss and parameter changes.
- `recovery/logs/generated_skill_invocations.json` proving generated skill use.

## Workflow
1. Import generated helper scripts from the skill root, not from the original WordNet source repository.
2. Build a tiny taxonomy fixture and validate its inventory.
3. Preprocess a reduced sample with a known collocation and inflected lookup forms.
4. Tag senses with context and explicit unresolved behavior.
5. Compute semantic distances and run one scalar optimizer step for a near/far threshold.
6. Write recovery artifacts and mechanism checks required by the Distiller recovery gate.

## Validation
Run `python scripts/recovery_harness.py --attempt-dir <attempt> --skills-root <skills_root>` followed by the Distiller recovery experiment validator.

## Limitations
This is a declared soft-mode proxy and does not claim to reproduce full WordNet inventory scale or the historical X-windows ConText interface.
