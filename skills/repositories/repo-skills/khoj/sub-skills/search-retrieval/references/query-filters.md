# Query Filters

Khoj supports structured query filters embedded in the same `q` string as the natural-language search. Search embeds the defiltered natural-language text, while database predicates use the filter terms extracted from the original query.

## Date Filters

Syntax uses `dt`, a comparator, and a quoted date phrase:

- Exact day/range: `dt:"1984-04-01"`, `dt="1984-04-01"`, or `dt=="1984-04-01"`
- After: `dt>"1984-04-01"`
- On or after: `dt>="1984-04-01"`
- Before: `dt<"1984-04-01"`
- On or before: `dt<="1984-04-01"`

Date strings must be inside straight or curly single/double quotes. Natural relative phrases are accepted in query filters, including examples such as `today`, `yesterday`, `last week`, `next month`, and `20 years later`. Parsed granularity becomes a half-open timestamp interval: exact dates cover the start of that day through the start of the next day; month/year phrases expand to month/year ranges.

Multiple date filters are ANDed by intersecting intervals. For example:

```text
planning notes dt>="1984-04-01" dt<"1984-05-01"
```

means entries dated from the start of April 1, 1984 up to but not including May 1, 1984. Non-intersecting ranges and unparseable dates produce no date predicate.

Date filtering depends on dates extracted during indexing. The extractor recognizes structured dates such as `1984-04-01`, `1984/04/01`, `01-04-1984`, `01/04/1984`, `01.04.1984`, and natural dates such as `1 April 1984`, `Apr 1984`, and two-digit year variants. Relative words inside content, such as `today`, are not indexed as dates.

`DateFilter.get_filter_terms()` reports terms in normalized single-quoted display form, such as `dt>='1984-04-01'`. `DateFilter.defilter()` removes matched date filters and collapses extra spaces.

## File Filters

Syntax:

- Include file/path pattern: `file:"incoming.org"`
- Exclude file/path pattern: `-file:"archive.org"`
- Wildcards are supported: `file:"notes/*.md"`, `-file:"*.tmp"`

Include filters are ORed together: any included path pattern can match. Exclude filters are ANDed as negated predicates. If include and exclude filters are both present, the final predicate is the included set minus excluded matches.

Patterns are converted to database regexes by escaping literal text and expanding `*` to `.*` and `?` to `.`. Matching is against the stored `file_path` field, not just the basename.

`FileFilter.get_filter_terms()` returns includes as plain strings and excludes with a leading `-`, for example:

```text
query -file:"drafts/*.md" file:"notes/*.md"
```

returns `notes/*.md` and `-drafts/*.md`. A known implementation edge case is that `FileFilter.defilter()` removes include filters but does not remove `-file:"..."` exclusions from the embedded query text. If no-results behavior looks odd with excluded files, inspect the defiltered query as well as filter terms.

## Word Filters

Syntax:

- Required word: `+"term"`
- Blocked word: `-"term"`

Word filter terms can contain letters, digits, underscores, and hyphens. Spaces and punctuation inside the quoted term do not match the current word-filter regex. Required terms add case-insensitive `raw contains term` predicates; blocked terms add negated case-insensitive predicates.

Example:

```text
what did the meeting decide +"roadmap" -"deprecated"
```

Search embeds `what did the meeting decide`; filtering requires `roadmap` in the raw entry and rejects entries containing `deprecated`.

## Combined Query Example

```text
release decisions dt>="2024-01-01" dt<"2024-04-01" file:"notes/*.md" -file:"notes/archive/*" +"roadmap" -"deprecated"
```

Expected interpretation:

- Embedded query text is the natural-language portion after each filter's defilter operation.
- Date predicates keep entries dated in Q1 2024.
- File predicates keep matching `notes/*.md` entries except those under `notes/archive/*`.
- Word predicates require `roadmap` and reject `deprecated` in raw entry text.

Use `scripts/inspect_query_filters.py` to display extracted terms, computed date range, and defiltered forms before debugging database state or model ranking.
