# Querying workflows

## Verify a saved model without a long run

```python
from paperai.models import Models
from paperai.query import Query

embeddings, db = Models.load("/data/papers")
try:
    Query.query(embeddings, db, "+hypertension -animal", 10, 0.25)
finally:
    Models.close(db)
```

The `Models.load` call opens the SQLite file and loads embeddings only when a
`config` or `config.json` is present. Use a temporary copy or read-only corpus
when testing. Query output includes title, publication, dates, ids, references,
and matching text; scores are model-dependent and should not be treated as
probabilities.

## Query syntax

- Plain terms perform the configured txtai similarity/keyword search.
- `+term` keeps only sections containing that term.
- `-term` removes sections containing that term.
- `threshold` removes results below the score threshold; lower it only after
  checking false negatives.
- `topn` is the number of article groups displayed, not necessarily the number
  of matched sections.
- `*` is a report-level all-article sentinel; in `Query.search` it intentionally
  returns no vector matches.

## API search response

Use the API when a caller needs structured metadata rather than Rich terminal
text. Pass `limit` and `threshold` as query parameters, and validate numeric
values before sending them. The API groups matching sections by article and
sorts articles by the sum of section scores.

## UI integration checklist

Keep UI code separate from package operation: load the model once, close the
SQLite connection when the app exits, and avoid rebuilding an index during a
request. Treat model loading and first-use downloads as startup operations with
a visible cache/error message. If Streamlit is unavailable, use the CLI or API
route rather than adding it to the core installation.
