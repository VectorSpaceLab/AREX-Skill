---
name: "data-and-rewards"
description: "Validate VLM-R1 JSONL datasets, map image roots, and choose or
  test reward methods."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-and-rewards

Use this sub-skill when you need to:
- validate single-image, multi-image, or text-only JSONL rows
- map relative image paths against paired image roots
- choose between file-level `reward_method` and row-level `accu_reward_method`
- explain answer formats for label, math, bbox, and OD fixtures
- run lightweight bbox scoring on tiny synthetic examples

## Start here
1. Read `references/data-formats.md`.
2. Read `references/reward-functions.md`.
3. Read `references/troubleshooting.md`.
4. Run `scripts/validate_jsonl_dataset.py` for schema checks.
5. Run `scripts/score_bbox_outputs.py` for tiny bbox fixtures.

## Route elsewhere
- Training command construction, launch flags, or DeepSpeed details -> `training-workflows`
- Model module interfaces or processor wiring -> `model-modules`
- Saved-output evaluation workflows -> `evaluation`

## What this sub-skill covers
- one JSON object per line
- `image` as a string or list of strings
- `conversations` with a question turn and an answer turn
- colon-separated file, image-root, and method pairing
- reward registry names: `accuracy`, `format`, `length`, `repetition`
- accuracy methods: `default`, `mcq`, `yes_no`, `llm`, `map`, `math`, `weighted_sum`, `od_ap`, `od_ap50`, `odLength`, `all_match`

## Guardrails
- Keep image paths relative to the paired image root.
- Keep answers concise; the loader wraps the stored answer in `<answer>...</answer>` internally.
- Do not tell future agents to inspect the source repository for these rules.
