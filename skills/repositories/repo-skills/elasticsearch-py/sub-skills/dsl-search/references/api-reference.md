# DSL API reference

## Query objects

`Q(name_or_query="match_all", **params)` creates a query. Common forms are
`Q("match", title="python")`, `Q("term", status="published")`, and
`Q({"range": {"year": {"gte": 2020}}})`. Combine query objects with `&`,
`|`, and `~`; render with `.to_dict()`.

## Search

`Search(using="default", index=None, **kwargs)` creates a request builder.
The useful chainable methods include:

- `.using(client_or_alias)` associates a client.
- `.index(...)` selects one or more indices.
- `.query(query_or_name, **params)`, `.filter(...)`, and `.exclude(...)` build
  the query/filter portions.
- `.sort(...)`, `.source(...)`, `.highlight(...)`, `.collapse(...)`,
  `.suggest(...)`, `.extra(...)`, and `.params(...)` add request options.
- `.aggs.bucket(name, agg_type, **params)` and `.aggs.metric(...)` build
  aggregations.
- `.to_dict()` returns a request body; `.execute()` sends the request.
- `.count()` sends a count request; `.scan()` uses the scan pattern for large
  result sets. Confirm the current installed signature before relying on less
  common execution helpers.

Search operations return a clone rather than mutating the original in the
usual chainable methods. Keep the rendered request as a reviewable artifact
when a query is complex.

## Documents and mappings

`Document` and `InnerDoc` classes declare `Text`, `Keyword`, `Date`, numeric,
object, nested, vector, and other field types. `Index` and `Mapping` represent
index configuration. A `Document` can define `Index.name`, settings, aliases,
and class-level `save`, `get`, `search`, and `init` operations. Use the same
client and connection explicitly in multi-cluster applications.

The DSL exports synchronous and asynchronous variants, including `AsyncSearch`,
`AsyncDocument`, `AsyncIndex`, `AsyncMapping`, `AsyncFacetedSearch`, and
`AsyncUpdateByQuery`. They preserve the request-builder ideas but require
awaiting network operations.
