# DSL troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValidationException` or `UnknownDslObject` while building | Misspelled query/aggregation/field type or invalid parameters | Check the installed DSL export and constructor signature; reduce to a minimal `Q`/field and inspect `.to_dict()`. |
| Query renders but server rejects it | Index mapping, server version, or API feature mismatch | Compare the request body with the target server version and mapping; test against an isolated index. |
| Search results have unexpected relevance | A clause was put in `filter` instead of `query`, or analyzer/mapping differs | Inspect the rendered bool query, field mapping, analyzer, and `minimum_should_match`; do not tune scores before checking mapping. |
| Aggregation is missing or fails | Field is analyzed text, unmapped, or has incompatible type | Use a keyword/date/numeric subfield or correct mapping and reindex; inspect `response.aggregations`. |
| `Document.init`/`save` fails | Missing privilege, wrong index name, immutable mapping, or no service | Validate connection/privileges and render mapping offline; use a new index/reindex for incompatible field changes. |
| Async DSL call is not awaitable | Used a synchronous DSL object/client or called a sync helper | Use `AsyncSearch`/`AsyncDocument` with `AsyncElasticsearch` and `await` execution; close the client. |
| Response access raises `KeyError` | Response shape differs by API/version or optional field is absent | Inspect `response.body`/typed attributes and check presence before access; do not assume every hit has `_source`. |
| Dynamic field names are unsafe | User input was inserted directly into query/field strings | Validate field names against an allow-list and pass values as parameters; never concatenate raw JSON. |
| DSL package optional behavior is missing | Feature needs an extra such as `numpy`, `pyarrow`, or vector-store support | Install only the extra for the selected feature and verify the import separately. |

A rendered request is the strongest offline assertion. A live cluster test must
also record server version, index mapping, privileges, and response shape.
