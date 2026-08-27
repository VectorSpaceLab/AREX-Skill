# FlashText Workflows

## Purpose

Read this when you want to actually use FlashText rather than only inspect its
API surface. The examples below are distilled from the README, docs, source,
and tests.

## 1. Exact keyword extraction and replacement

Use the default processor when you want fast phrase matching with clean-name
output.

```python
from flashtext import KeywordProcessor

kp = KeywordProcessor()
kp.add_keyword("Big Apple", "New York")
kp.add_keyword("Bay Area")

print(kp.extract_keywords("I love Big Apple and Bay Area."))
# ['New York', 'Bay Area']

print(kp.replace_keywords("I love Big Apple and Bay Area."))
# I love New York and Bay Area.
```

Good fit:

- short sentences or documents;
- clean-name normalization;
- direct keyword replacement without regular expressions.

## 2. Case sensitivity and spans

Use `case_sensitive=True` when you need the stored case to matter.
Use `span_info=True` when the caller needs start and end offsets.

```python
kp = KeywordProcessor(case_sensitive=True)
kp.add_keyword("Big Apple", "New York")
kp.add_keyword("Bay Area")

print(kp.extract_keywords("I love big Apple and Bay Area."))
# ['Bay Area']

print(kp.extract_keywords("I love Big Apple and Bay Area.", span_info=True))
# [('New York', 7, 16), ('Bay Area', 21, 29)]
```

Remember:

- `span_info=True` changes the return shape to tuples.
- The offsets are character indices in the matched sentence.

## 3. Fuzzy matching with `max_cost`

Set `max_cost` when small typos or insertions/deletions should still match.
Keep the budget small and deliberate.

```python
kp = KeywordProcessor()
kp.add_keyword("skype", "messenger")

print(kp.extract_keywords("hello, do you have skpe ?", span_info=True, max_cost=1))
# [('messenger', 19, 23)]

print(kp.replace_keywords("hello, do you have skpe ?", max_cost=1))
# hello, do you have messenger ?
```

Best practice:

- start with `max_cost=1`;
- increase only if the matching task really needs typo tolerance;
- verify that longer phrases still match the intended span.

## 4. Load keywords from files, lists, and dictionaries

Use the bulk-loading helpers when the source data already lives in a simple
text file or Python container.

```python
kp = KeywordProcessor()
kp.add_keywords_from_dict({
    "java": ["java_2e", "java programing"],
    "product management": ["PM", "product manager"],
})
kp.add_keywords_from_list(["python"])
```

```python
kp.add_keyword_from_file("keywords.txt")
```

Input shapes are documented in `references/data-formats.md`.

## 5. Remove, inspect, and normalize

`KeywordProcessor` behaves like a small dictionary in the common cases.

```python
kp = KeywordProcessor()
kp.add_keyword("j2ee", "Java")
kp.add_keyword("colour", "color")

print(len(kp))
# 2
print("colour" in kp)
# True
print(kp.get_all_keywords())
# {'colour': 'color', 'j2ee': 'Java'}

kp.remove_keyword("j2ee")
```

Use this pattern when you need to keep a keyword registry synchronized with a
user-facing taxonomy or synonym list.

## 6. Tune word boundaries

By default, FlashText treats letters, digits, and underscore as part of a word.
Use the boundary helpers when punctuation should be matched as part of the
keyword.

```python
kp = KeywordProcessor()
kp.add_keyword("Big Apple")
print(kp.extract_keywords("I love Big Apple/Bay Area."))
# ['Big Apple']

kp.add_non_word_boundary("/")
print(kp.extract_keywords("I love Big Apple/Bay Area."))
# []
```

Read the boundary notes in `references/data-formats.md` and the troubleshooting
section before changing the default set.

## 7. Fast validation loop

When a workflow changes or a user reports a mismatch, run the bundled smoke
check before opening the full test suite.

```bash
python scripts/check_install.py
```

Use `python scripts/check_install.py --json` if you want a compact machine-
readable summary.
