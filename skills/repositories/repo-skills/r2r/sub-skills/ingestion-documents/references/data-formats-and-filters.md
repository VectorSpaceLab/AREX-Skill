# Data Formats and Filters

## Document format guidance

R2R documents can come from local files, inline text, prebuilt chunks, or object-storage URLs. The repository evidence and docs cover common text, PDF, image, audio, and JSON-style inputs.

## Filter grammar

Use dictionary filters for list/search/delete-by-filter operations.

Common shapes:

- top-level fields such as `id`, `document_id`, or `collection_ids`
- metadata paths such as `metadata.title`
- nested conjunctions with `$and` and `$or`
- comparisons such as `$eq`, `$gt`, and `$in`
- text containment with `$contains` where the API supports it

## Example filters

```python
{
  "$and": [
    {"metadata.source": {"$eq": "docs"}},
    {"metadata.year": {"$gt": 2023}}
  ]
}
```

```python
{
  "collection_ids": {"$in": ["collection-id-a", "collection-id-b"]},
  "metadata.tags": {"$contains": "rag"}
}
```

## Shape reminders

- Use a list of strings for `chunks`.
- Use a dictionary for document metadata.
- Pass `collection_ids` as a list, not a scalar.
- Keep filters aligned with the field names emitted by the API or source schema.
