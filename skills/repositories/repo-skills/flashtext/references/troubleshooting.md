# FlashText Troubleshooting

## Purpose

Read this when FlashText fails to import, a load helper rejects your data, or a
keyword does not match the way you expected.

## Common failures

| Symptom | Likely cause | Recovery | Next check |
| --- | --- | --- | --- |
| `ModuleNotFoundError` / `ImportError` for `flashtext` | The package is not installed in the active Python environment, or the wrong environment is active. | Install with `python -m pip install flashtext` or, from a checkout, `python -m pip install -e .`. Then rerun `python scripts/check_install.py`. | `scripts/check_install.py` |
| `IOError: Invalid file path ...` | `add_keyword_from_file()` received a missing or wrong relative path. | Confirm the file exists, use a path relative to the current working directory, or switch to an absolute path. | `references/data-formats.md` |
| `AttributeError: Value of key ... should be a list` | A dictionary value was a string, tuple, set, or other non-list object. | Change the value to a real `list[str]` of variants. | `references/data-formats.md` |
| `AttributeError: keyword_list should be a list` | `add_keywords_from_list()` or `remove_keywords_from_list()` got a string or other non-list input. | Wrap the keywords in a Python list. | `references/data-formats.md` |
| `replace_keywords()` crashes or prints tuple-like text | Clean names were stored as tuples, which work for extraction but not string replacement. | Keep clean names as strings when you plan to call `replace_keywords()`. Use tuple clean names only if you intend to extract structured metadata. | `references/api-reference.md` |
| A keyword should match, but extraction returns nothing | Case mode or word boundaries are filtering it out. | Check `case_sensitive`, then check whether punctuation needs `add_non_word_boundary()` or a custom boundary set. | `references/workflows.md` |
| Fuzzy matching still misses obvious typos | `max_cost` is too small, or the phrase is longer than the budget you allowed. | Increase `max_cost` carefully and re-test the smallest failing example first. | `references/workflows.md` |
| `iter(kp)` raises `NotImplementedError` | Iteration is intentionally disabled. | Use `kp.get_all_keywords()` instead. | `references/api-reference.md` |
| File-loading lines with `=>` behave oddly | The file format is line-oriented and the keyword side is not stripped when `=>` is present. | Keep lines simple, use one arrow per line, and avoid extra spaces around the arrow. | `references/data-formats.md` |
| A line beginning with `#` is treated as a keyword | FlashText keyword files do not support comments. | Pre-clean the file or remove comment lines before loading. | `references/data-formats.md` |

## Recovery pattern

1. Reduce the problem to one failing keyword or one failing line.
2. Re-run `python scripts/check_install.py` to confirm the package still works.
3. Compare the failing input against `references/data-formats.md` and
   `references/workflows.md`.
4. If the issue is still unclear, reproduce it with a tiny standalone snippet
   before changing the full dataset or registry.
