---
name: flashtext
description: "Routes FlashText tasks for keyword extraction, replacement, fuzzy
  matching, keyword loading, and keyword-inspection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlashText

Use this skill when a request names **FlashText** or asks to extract, replace,
load, inspect, or fuzzily match keywords with `KeywordProcessor`.

This repository is small enough that one router covers the whole package.
Read the bundled references for exact API details instead of reopening the
original checkout.

## Install and verify

- Public install: `python -m pip install flashtext`
- From a checkout: `python -m pip install -e .`
- Safe smoke check: `python scripts/check_install.py`
- JSON smoke output: `python scripts/check_install.py --json`
- Minimal import check:
  `python -I -c "from flashtext import KeywordProcessor; print(KeywordProcessor().__class__.__name__)"`

If you are checking whether this skill still matches the repository snapshot,
read `references/repo-provenance.md` before making that call.

## Route map

- Need to add, remove, count, or inspect keywords with dictionary-like
  behavior (`len`, `in`, `[]`, `get_keyword`, `get_all_keywords`)? Read
  `references/api-reference.md` and `references/workflows.md`.
- Need sentence extraction, replacement, spans, `case_sensitive`, or fuzzy
  `max_cost` behavior? Start with `references/workflows.md`, then open
  `references/api-reference.md` for exact signatures and return shapes.
- Need to load keywords from a file, list, or dictionary, or you want the
  expected input shapes? Read `references/data-formats.md`.
- Need to debug import errors, bad file paths, malformed list/dict shapes,
  `replace_keywords` with tuple clean names, or missed matches caused by word
  boundaries or case handling? Read `references/troubleshooting.md`, then rerun
  `scripts/check_install.py`.
- Need to compare the current checkout against the recorded baseline? Read
  `references/repo-provenance.md`.

## Typical request phrases

- "extract keywords from this sentence"
- "replace keywords with clean names"
- "show spans for each match"
- "make matching case sensitive"
- "load keywords from a file"
- "load from a list or dictionary"
- "remove a keyword variant"
- "allow punctuation like / inside keywords"
- "debug why a keyword did not match"
- "check whether the package is installed correctly"

## What to read or run next

- Use `references/workflows.md` for step-by-step usage patterns.
- Use `references/api-reference.md` when you need the exact signature or return
  type for a method on `KeywordProcessor`.
- Use `references/data-formats.md` when shaping file, list, or dictionary
  inputs.
- Use `references/troubleshooting.md` for predictable input and matching
  failures.
- Run `scripts/check_install.py` whenever you need a quick install/import/
  smoke verification.

## What this skill does not cover

- No CLI entry point is shipped by the package.
- No network service, model backend, or accelerator-specific workflow is
  involved.
- No training, benchmarking, or docs-build workflow is part of the runtime
  route.

## Working rule

Keep runtime instructions self-contained. Use the bundled references and
script instead of the original repository when you need API details,
data-shape reminders, or a fast validation check.
