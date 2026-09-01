---
name: ffn_concept_grouping
description: Group top promoted vocabulary tokens into human-readable concept labels with purity and unresolved-token evidence.
---

# ffn_concept_grouping

Use this skill for the FFN value-vector concept-promotion workflow when its input contract matches the module plan. It should be used during recovery only with current-attempt artifacts, generated fixtures, model weights from allowed caches, or paper-derived descriptions. Do not read the original source repository.

## Inputs

Structured JSON data matching the module contract: matrices, vocabulary tokens, concept lexicons, activations, or runtime handoff paths as appropriate.

## Outputs

Deterministic JSON records suitable for downstream modules and recovery validation. Outputs preserve provenance, include numeric scores where relevant, and expose failed checks rather than hiding them.

## Workflow

Validate dimensions and required fields, execute the paper-inspired operation, write JSON output, and use the output as evidence for the next module. The operation preserves the central paper insight that FFN value vectors can be interpreted by their vocabulary-logit contribution and by activation-conditioned promotion of concept tokens.

## Validation

Run the script fixture with `python scripts/group_concepts.py --fixture` when supported and run the tests with the Distiller skill-tree validator.

## Limitations

This is a reusable deterministic helper, not a full language-model runner. Full-scale claims require real model weights; soft-mode recovery may use deterministic proxy fixtures only when declared and mechanism-faithful.
