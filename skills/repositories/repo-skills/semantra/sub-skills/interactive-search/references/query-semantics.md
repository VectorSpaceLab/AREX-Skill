# Query Semantics

## Purpose

Read this to explain Semantra's browser search grammar, preference tags,
normalization, result scores, and why semantic search behaves differently from
exact keyword search.

## Query parser grammar

The web UI parses a query with this shape:

```text
[+|-][number] phrase [+|-][number] phrase ...
```

Examples:

| Search bar text | Parsed intent |
| --- | --- |
| `ghost requesting revenge` | one positive phrase |
| `economic growth + unchecked capitalism` | two positive phrases |
| `economic growth - unchecked capitalism` | one positive and one negative phrase |
| `economic growth - unchecked capitalism + war` | two positive phrases and one negative phrase |
| `+3 dogs are nice -2 cats are mean` | explicit numeric positive and negative weights |

Use the bundled parser helper to show the shape without starting the web UI:

```sh
python scripts/parse_semantra_query.py "economic growth - unchecked capitalism + war"
```

## Weight normalization

Before sending a query to the server, the UI counts positive query phrases,
negative query phrases, positively tagged results, and negatively tagged
results. It then splits fixed positive and negative ratios:

- positive ratio: `0.61803398875`;
- negative ratio: `0.38196601125`.

Each positive typed query gets its raw weight multiplied by
`positive_ratio / positive_item_count`. Each negative typed query gets its raw
weight multiplied by `negative_ratio / negative_item_count`. Preference tags are
included in the item counts and then sent separately with their own weights.

This is not the same as normalizing by total absolute raw weight. Explicit
numeric weights still matter, but they are multiplied by the per-item ratio
share.

## Preference tags

Clicking a `+` or `-` on a search result creates a preference tag below the
search bar. The search bar turns stale/yellow until the user reruns the search.
When rerun, Semantra combines:

- embeddings of the typed query phrases; and
- stored embeddings of the tagged result windows.

Positive tags pull the query vector toward similar windows. Negative tags push
it away from similar windows. Removing a tag removes that stored embedding from
the next query.

## Result scores

Semantra always returns the nearest windows for a non-empty query; unlike a
keyword search, irrelevant queries still have nearest neighbors. Low scores do
not mean the system failed; they may simply mean every window is weakly related.
Scores around `0.50` can be useful semantic matches depending on the model and
corpus.

Exact search ranks by cosine similarity. The default Annoy route retrieves from
an angular nearest-neighbor index and converts Annoy distances with:

```text
score = 1 - distance**2 / 2
```

The optional SVM route trains a linear classifier per query against document
window embeddings and uses the decision function as a similarity-like score.

## Search iteration pattern

1. Start broad: `foreign policy`.
2. Add a positive concept: `foreign policy + economic growth`.
3. Subtract a confusing concept: `foreign policy + economic growth - war`.
4. Positively tag one result that captures the intent.
5. Negatively tag a misleading result.
6. Rerun the query and switch between grouped-by-file and individual-result
   views.

## UI state that affects interpretation

- Yellow search bar: query/tags changed and results are stale.
- Filename filter: hides files whose names do not match the filter.
- Eye button: restricts results to the active document.
- Grouped view: sorts files by average result relevance and shows windows under
  each file.
- Results view: flattens and sorts individual windows by relevance.
- Collapsed files: results may be hidden until expanded.

When debugging user complaints, ask for the exact query text, active tags,
filter state, and view mode before assuming a model or indexing problem.
