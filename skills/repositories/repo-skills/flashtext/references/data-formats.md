# FlashText Data Formats

## Purpose

Read this when a task needs to build the inputs for `KeywordProcessor` or to
understand why a load/remove call accepts some shapes and rejects others.

## Keyword dictionary format

`add_keywords_from_dict()` and `remove_keywords_from_dict()` expect a mapping
of **clean name** to a **list of keyword variants**:

```python
{
    "java": ["java_2e", "java programing"],
    "product management": ["PM", "product manager"],
}
```

Notes:

- Each value must be a real `list`, not a tuple, set, or string.
- Every variant in the list is treated as a keyword that maps back to the clean
  name.
- When `case_sensitive=False` the stored keys are lowercased internally.

## Keyword list format

`add_keywords_from_list()` and `remove_keywords_from_list()` expect a plain
Python `list[str]`:

```python
["java", "python", "Big Apple"]
```

Notes:

- Each entry maps to itself as the clean name.
- A non-list input raises `AttributeError`.

## Keyword file format

`add_keyword_from_file()` reads one keyword per line from a UTF-8 text file.
It supports two line shapes:

```text
java_2e=>java
product management techniques=>product management
```

or:

```text
java
python
c++
```

Notes:

- Keep the `keyword=>clean_name` form to **one arrow per line**.
- The keyword side is not stripped when `=>` is present, so avoid spaces around
  the arrow.
- Blank lines are ignored because empty keywords are rejected.
- There is no comment syntax; a line beginning with `#` is treated as a keyword
  unless you filter it out first.

## Boundary and normalization reminders

- `case_sensitive=False` lowercases keys and lookups.
- `non_word_boundaries` defaults to letters, digits, and underscore.
- Use `add_non_word_boundary()` or `set_non_word_boundaries()` when your
  keyword contains punctuation that should behave like a word character.
- `replace_keywords()` expects clean names that can be concatenated into a
  string; tuple clean names are for extraction only.
