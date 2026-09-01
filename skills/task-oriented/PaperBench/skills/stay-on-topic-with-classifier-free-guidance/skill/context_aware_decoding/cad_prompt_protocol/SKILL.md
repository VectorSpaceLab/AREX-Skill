---
name: cad_prompt_protocol
description: Build and validate context-aware decoding prompt parts with separated evidence context, query, and generation prefix.
---

# CAD Prompt Protocol

Use this skill when implementing Context-aware Decoding (CAD) or a recovery experiment that must compare a context-conditioned language-model distribution against a query-only prior distribution. Do not use it to evaluate answers or choose tokens.

## Inputs
- `context`: evidence text that should be upweighted.
- `query`: question, instruction, or task prefix that appears in both CAD branches.
- `prefix`: generated text so far.
- `task`: optional task label.

## Outputs
A structured prompt record with `full_prompt`, `prior_prompt`, and metadata proving the context is absent from the prior branch.

## Workflow
1. Check that context and query are non-empty strings.
2. Keep context separate from query.
3. Build the full branch from context, query, and prefix.
4. Build the prior branch from query and prefix only.
5. Return diagnostics confirming branch separation.

## Validation
Run `python tests/test_prompt_protocol.py` or Distiller `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not call a language model and must not insert gold answers, evaluation labels, or final-answer markers into prompts.
