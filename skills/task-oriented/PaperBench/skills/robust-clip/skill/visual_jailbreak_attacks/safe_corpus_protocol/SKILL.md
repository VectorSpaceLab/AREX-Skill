---
name: safe_corpus_protocol
description: Build and validate harmless corpus splits that mirror visual jailbreak optimization and held-out evaluation protocols.
---

# Safe Corpus Protocol

Use this skill when a recovery or evaluation needs a harmless stand-in for the visual jailbreak paper's few-shot optimization corpus and held-out prompt protocol. Do not use it to create, store, or evaluate real harmful instructions; it is designed for symbolic or safety-neutral proxy experiments.

## Inputs

- `train_targets`: safe strings used only by an optimizer.
- `heldout_prompts`: safe prompts used only by evaluation.
- Optional `categories`: category labels for held-out prompts.
- Optional `disallowed_markers`: exact substrings that must not appear in any item.

## Outputs

- A validated JSON object with `train_targets`, `heldout_prompts`, `categories`, `safety`, and `split_checks`.
- A CLI validation report when using `scripts/corpus_protocol.py`.

## Workflow

1. Normalize targets and prompts into records with stable IDs.
2. Reject empty text, duplicate IDs, train/evaluation overlap, and configured disallowed markers.
3. Preserve category labels for later per-category jailbreak proxy scoring.
4. Emit deterministic JSON so downstream recovery can record the generated data item.
5. Treat train/evaluation separation as a mechanism check: the proxy only demonstrates generalization if held-out prompts are distinct from optimization targets.

## Validation

Run:

```bash
python scripts/corpus_protocol.py --self-test
```

The tests in `tests/test_corpus_protocol.py` exercise valid corpus creation, overlap rejection, duplicate ID rejection, and marker filtering.

## Limitations

This skill does not judge real-world safety. It only enforces conservative structural checks for harmless proxy fixtures and should not be used to assemble harmful content.
