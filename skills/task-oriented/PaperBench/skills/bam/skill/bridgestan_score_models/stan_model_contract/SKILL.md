---
name: stan_model_contract
description: Extract a structured contract from simple Stan programs so score-model workflows can identify data, constrained parameters, transforms, model terms, and generated quantities.
---

# Stan Model Contract

Use this skill when a recovery or algorithm needs a lightweight, language-neutral contract for a small Stan model. Do not use it as a general Stan compiler or full parser.

## Inputs
- Stan source text or a path to a `.stan` file.
- Optional observed data dictionary for downstream validation.

## Outputs
- JSON with `data`, `parameters`, `transformed_parameters`, `model_terms`, and `generated_quantities`.
- Diagnostics for unsupported or missing sections.

## Workflow
1. Read the Stan source.
2. Call `scripts/stan_contract.py --stan <path> --output <json>`.
3. Inspect the output contract before passing it to transform or score-evaluation modules.
4. Treat unsupported syntax as a blocker for this reduced parser, not as evidence about real BridgeStan.

## Validation
Run `python tests/test_stan_contract.py` from this skill directory.

## Limitations
The parser intentionally supports the Bernoulli-style recovery subset: scalar bounded real parameters, integer data arrays, simple transformed-parameter assignments, distribution statements, and generated-quantity assignments.
