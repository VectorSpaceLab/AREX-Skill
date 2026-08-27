# DSL workflows

## Compose a search request

```python
from elasticsearch.dsl import Q, Search

text = Q("multi_match", query="python client", fields=["title^2", "body"])
recent = Q("range", published_at={"gte": "now-30d"})
request = (
    Search(index="books")
    .query(text & recent)
    .filter("term", status="published")
    .source(includes=["title", "published_at"], excludes=["internal_notes"])
    .sort({"published_at": "desc"})
    .extra(track_total_hits=True)
)
body = request.to_dict()
```

Use `.filter()` for constraints that should not affect relevance, and use
`.query()` for scoring clauses. Add `request = request[0:20]` for a simple
from/size slice, or use explicit pagination/search-after options when the
result set is large. Do not concatenate user input into raw JSON; pass values as
DSL parameters and validate field names against an allow-list.

## Aggregations

```python
request.aggs.bucket("by_status", "terms", field="status").metric(
    "avg_year", "avg", field="year"
)
body = request.to_dict()
```

Name buckets and metrics deterministically, and inspect `response.aggregations`
only after checking that the server mapping supports the requested field type.

## Typed persistence

```python
from elasticsearch.dsl import Date, Document, Keyword, Text

class Book(Document):
    title = Text()
    status = Keyword()
    published_at = Date()

    class Index:
        name = "books"

# await Book.init(using=async_client) or Book.init(using=client)
# book = Book(title="Python", status="published")
# book.save(using=client)
```

Create mappings in an isolated index first; changing field types in place is
usually not possible without reindexing. Use `InnerDoc` for nested structured
values and explicit field types for correct serialization and query behavior.

## Raw client migration

Render a `Search` or `Q` with `.to_dict()` and pass the resulting body to a raw
client API only when the raw method's parameter shape requires it. Conversely,
start from an existing body with `Q(body)` when migrating incrementally. Keep
client setup and transport options in the client-operations route.
