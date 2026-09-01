---
name: toxigen_prompt_protocol
description: Build and validate ToxiGen-style balanced identity-label demonstration prompts for implicit toxicity generation and recovery experiments.
---

# ToxiGen Prompt Protocol

Use this skill when a task needs to construct or audit ToxiGen-style prompts from labeled demonstrations. It is appropriate for paper recovery, dataset construction checks, and controlled prompt fixtures where identity group and toxic/benign label balance matter.

Do not use this skill to generate model continuations, run ALICE decoding, score classifier outputs, or train toxicity classifiers. Those are downstream modules.

## Inputs

- Demonstration records with `text`, `group`, `label`, and optional `source`.
- Prompt parameters: demonstrations per prompt, random seed, and optional forbidden explicit terms.
- Optional group alias map when identity mentions use variants.

## Outputs

- Prompt records with stable `prompt_id`, `group`, `label`, sampled demonstrations, prompt text, and source provenance.
- Validation summary with counts by group/label, balance status, identity coverage, short buckets, and explicit-term violations.

## Workflow

1. Normalize labels to `toxic` and `benign`.
2. Group demonstrations by `(group, label)`.
3. Sample a fixed number of demonstrations per bucket with a deterministic seed.
4. Format prompts as one demonstration per bullet line followed by a final bullet marker for continuation.
5. Validate each record for group alias mention and explicit-term leakage.
6. Carry source file provenance into every prompt record so recovery can prove which resource files were used.

## Validation

Run:

```bash
python scripts/prompt_protocol.py --self-test
python tests/test_prompt_protocol.py
```

The test fixture checks deterministic sampling, identity coverage, explicit-term detection, and balance accounting without external packages.

## Limitations

This skill only constructs prompt records. It does not guarantee generated text quality, human-likeness, classifier attack success, or downstream classifier improvement.
