---
name: dpo_preference_data_contract
description: Normalize pairwise preference records into prompt, chosen, rejected, and metadata fields for Direct Preference Optimization training.
---

# DPO Preference Data Contract

Use this skill when preparing preference data for Direct Preference Optimization (DPO) or when validating a reduced DPO recovery experiment. Do not use it for unpaired reward-model data or ranking tasks that cannot identify a preferred and dispreferred response for the same prompt.

## Inputs

- Explicit records with `prompt`, `chosen`, and `rejected` strings.
- HH-style records with full conversation strings under `chosen` and `rejected`, sharing a prompt prefix ending in `\n\nAssistant:`.
- Optional metadata: `source`, `pair_id`, or split names.

## Outputs

A list of dictionaries with this contract:

```json
{"prompt": "...", "chosen": "...", "rejected": "...", "pair_id": "...", "source": "..."}
```

The output preserves chosen/rejected direction. It does not tokenize, score, or train a model.

## Workflow

1. Inspect each raw item and determine whether it is explicit or HH-style.
2. Validate non-empty prompt, chosen response, and rejected response.
3. For HH-style strings, split at the last `\n\nAssistant:` marker and require the chosen and rejected strings to share the same prompt prefix.
4. Reject identical chosen and rejected responses.
5. Emit normalized examples with stable pair ids and source metadata.

## Validation

Run:

```bash
python scripts/preference_data.py --self-test
python tests/test_preference_data.py
```

## Limitations

This skill only defines the data contract. It intentionally does not infer preferences from scores unless the caller has already converted scores into chosen/rejected pairs. It must not read the original DPO repository during recovery.