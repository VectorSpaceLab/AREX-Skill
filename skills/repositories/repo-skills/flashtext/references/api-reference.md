# FlashText API Reference

## Purpose

Read this when you need the exact `KeywordProcessor` signatures, return
shapes, or dictionary-like behavior. The facts below were verified from the
live `flashtext` 2.7 install and the source file `flashtext/keyword.py`.

## Core object protocol

| Signature | Behavior |
| --- | --- |
| `KeywordProcessor(case_sensitive=False)` | Creates a trie-backed processor. The default search is case-insensitive and normalizes stored keywords and lookups to lowercase. |
| `len(kp)` | Returns the number of distinct keywords stored in the trie. |
| `word in kp` | Returns `True` when `word` is stored under the active case mode. |
| `kp[word]` / `kp.get_keyword(word)` | Returns the clean name for `word`, or `None` if the keyword is missing. |
| `kp[word] = clean_name` / `kp.add_keyword(keyword, clean_name=None)` | Adds one keyword. If `clean_name` is omitted, the keyword maps to itself. Returns `True` for a new keyword and `False` when the keyword already existed. |
| `del kp[word]` / `kp.remove_keyword(keyword)` | Removes one keyword. Returns `True` when removal succeeds and `False` when the keyword is missing. |
| `iter(kp)` | Raises `NotImplementedError`. Use `get_all_keywords()` instead. |

## Boundary and inspection helpers

| Signature | Behavior |
| --- | --- |
| `kp.set_non_word_boundaries(non_word_boundaries)` | Replaces the whole set of characters treated as part of a word. Pass a `set[str]` of single-character strings. |
| `kp.add_non_word_boundary(character)` | Adds one character to the word-character set. |
| `kp.get_all_keywords(term_so_far='', current_dict=None)` | Recursively returns a `dict` mapping stored keyword variants to clean names. In case-insensitive mode the keys are lowercased. |
| `kp.get_next_word(sentence)` | Returns the next contiguous word characters from the start of `sentence`. |

## Loading and bulk mutation helpers

| Signature | Behavior |
| --- | --- |
| `kp.add_keyword_from_file(keyword_file, encoding='utf-8')` | Reads a UTF-8 text file containing either `keyword` or `keyword=>clean_name` lines. Raises `IOError` when the path is invalid. |
| `kp.add_keywords_from_dict(keyword_dict)` | Accepts a mapping of clean name to `list[str]` variants. Raises `AttributeError` if any value is not a list. |
| `kp.remove_keywords_from_dict(keyword_dict)` | Same input shape as `add_keywords_from_dict()`, but removes each variant. Raises `AttributeError` for non-list values. |
| `kp.add_keywords_from_list(keyword_list)` | Accepts a plain `list[str]` and maps each keyword to itself. Raises `AttributeError` if the input is not a list. |
| `kp.remove_keywords_from_list(keyword_list)` | Removes each keyword in a plain `list[str]`. Raises `AttributeError` if the input is not a list. |

## Matching helpers

| Signature | Behavior |
| --- | --- |
| `kp.extract_keywords(sentence, span_info=False, max_cost=0)` | Returns a list of clean names. With `span_info=True`, returns `(clean_name, start, end)` tuples. `max_cost` enables fuzzy matching with Levenshtein distance. Empty input returns `[]`. |
| `kp.replace_keywords(sentence, max_cost=0)` | Returns a new string with matched keywords replaced by their clean names. Empty input is returned unchanged. |
| `kp.levensthein(word, max_cost=2, start_node=None)` | Internal/fuzzy helper generator used by the extraction and replacement code. The misspelling is part of the public API. |
| `kp._levenshtein_rec(...)` | Internal recursive helper. Only inspect this when debugging fuzzy matching internals. |

## Verified behavioral notes

- `extract_keywords()` uses the stored clean name, not the original keyword.
- `replace_keywords()` preserves unmatched text from the original sentence.
- `case_sensitive=False` lowers both stored keywords and lookups.
- `span_info=True` changes the return type but not the matching logic.
- `replace_keywords()` does **not** support tuple clean names.
