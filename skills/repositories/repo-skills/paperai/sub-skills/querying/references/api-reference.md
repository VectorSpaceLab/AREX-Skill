# Querying API reference

Signatures were checked against `paperai` 2.6.0.

## Query helpers

```python
Query.search(embeddings, cur, query, topn, threshold)
Query.highlights(results, topn)
Query.documents(results, topn)
Query.query(embeddings, db, query, topn, threshold)
Query.run(query, topn=None, path=None, threshold=None)
Query.authors(authors)
Query.date(date)
Query.text(text)
```

`Query.search` returns tuples `(section_id, score, article_id, text)`. `topn`
is multiplied internally to account for duplicate section matches. `threshold`
defaults to `0.25` when `None`. Tokens beginning with `+` are required and
tokens beginning with `-` are prohibited; these checks are applied against the
section text after search. Weighted indexes tokenize the query before search.

`Query.documents` groups sections by article and retains descending section
scores; it returns at most `topn` articles. `Query.highlights` keeps results at
or above `0.1` and delegates ranking to `Highlights.build`, returning at most
five highlights. `Query.date` formats full dates as `YYYY-MM-DD` and January 1
placeholder dates as `YYYY`; invalid values are returned unchanged.

## Enriched API

```python
API.search(self, query, request=None)
```

When an embeddings model is configured, the result is a list of article objects:

```json
{
  "id": "article-id",
  "score": 0.91,
  "title": "Article title",
  "published": "2024-05-02",
  "publication": "Journal",
  "entry": "entry-date",
  "reference": "source-reference",
  "matches": ["matching section text"]
}
```

The optional request query parameters are `limit` and `threshold`; limit is
capped/parsed by txtai's API helper and defaults to 10 when no request exists.
An API object without configured embeddings returns `None`.
