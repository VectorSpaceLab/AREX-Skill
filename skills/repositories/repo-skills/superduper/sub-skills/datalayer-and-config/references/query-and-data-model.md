# Query and Data Model

Use this reference when a task needs to define records, schemas, table components, or backend queries before a Superduper model/listener/vector workflow is applied.

## Core objects

| Object | Verified signature or shape | Use |
| --- | --- | --- |
| `Document` | `Document(*args, schema=None, db=None, **kwargs)` | Dict-like wrapper that can encode/decode values with a `Schema` and a database context. |
| `Schema` | `Schema(fields: Dict[str, BaseDataType])` | Describes column/key datatypes and encoders. |
| `Table` | `Table(identifier, *, fields=None, primary_id="id", data=None, path=None, is_component=False)` | Component that declares a backend table and optional schema fields. |
| `Base` | subclass with typed fields | Dataclass-like base for typed data records that can be inserted through `db.insert`. |
| `Datalayer.__getitem__` | `db["table_name"]` | Creates a query object scoped to one table. |

`Component`, `Model`, `Listener`, and `VectorIndex` also serialize through the same `Base`/`Document` machinery, but their workflow ownership belongs to sibling sub-skills.

## Datatypes and schema fields

Common datatype choices:

- Primitive string aliases in table fields: `"str"`, `"int"`, `"float"`, `"bool"`, `"json"`.
- Vector aliases: `"vector[int:300]"`, `"vector[float:32]"`, or similar dtype/shape strings when model outputs are vectors.
- Public datatype classes include `JSON()`, `Pickle()`, `Dill()`, `File()`, `Array(dtype="float64", shape=...)`, and `Vector(dtype="float64", shape=...)`.
- Use explicit vector dimensions before wiring a `VectorIndex`; a dimension mismatch usually fails later during listener/vector-search execution.

Example table declaration:

```python
from superduper import Table

documents = Table(
    "documents",
    fields={
        "id": "str",
        "text": "str",
        "label": "int",
    },
)
db.apply(documents)
```

Typed records can also be defined with `Base`:

```python
from superduper import Base

class DocumentRecord(Base):
    id: str
    text: str
    label: int

items = [DocumentRecord(id="a", text="hello", label=1)]
db.insert(items)
```

`db.insert` auto-creates metadata for the record class when needed. Use explicit `Table` components when table schema, primary id, or workflow clarity matters.

## Query entrypoint and common operations

Start from `db[table_name]`:

```python
table = db["documents"]
query = table.select()
rows = query.execute()
```

Common query methods are chained from query objects:

| Operation | Typical shape | Notes |
| --- | --- | --- |
| insert | `db["documents"].insert([{...}, {...}])` | Inserts dict-like rows into the selected table. |
| select | `db["documents"].select()` | Returns all selected rows when executed. |
| filter | `db["documents"].select().filter(db["documents"]["label"] == 1)` | Uses query field operators; keep backend support in mind. |
| get | `db["documents"].get("id-value")` | Retrieves one record by primary id on supporting backends. |
| replace | `db["documents"].replace(condition, row)` | Backend-specific condition shape; test on scratch data first. |
| update | `db["documents"].update(condition, key, value)` | Mutating operation; prefer scratch verification. |
| delete | `db["documents"].delete(condition)` | Mutating operation; use carefully. |
| outputs | `db["documents"].outputs(...)` | Accesses listener/model output columns/tables. |
| missing_outputs | `db["documents"].missing_outputs(...)` | Useful before rerunning listeners. |
| like | `db["documents"].like({...}, vector_index="idx", n=10)` | Vector retrieval route; use the vector sub-skill for full recipes. |

Call `.execute()` only after constructing the query shape. Some backends return custom cursor/list wrappers; coerce to `list(...)` when a task needs indexing or deterministic assertions.

## Safe mutation pattern

Use scratch/local backends for experimentation:

```python
from superduper import superduper

db = superduper("mongomock://scratch", force_apply=True, initialize_cluster=False)
try:
    db["documents"].insert([{"id": "1", "text": "hello"}])
    rows = list(db["documents"].select().execute())
    assert rows
finally:
    # Only for scratch DBs you created for this run.
    db.drop(force=True, data=True)
```

Do not run `drop(force=True)` on shared MongoDB, SQL, Snowflake, Redis, or production URIs. For real stores, ask the user for an explicit destructive-operation confirmation and prefer `db.plan(...)` before `db.apply(...)`.

## Output tables and component metadata

- Listener and vector workflows write under the configured `output_prefix`, default `_outputs__`.
- `db.show()` lists components and statuses, not arbitrary data rows.
- `db.load(component, identifier, version=-1)` retrieves the latest saved component version.
- `uuid`/`huuid` can identify component versions when identifiers alone are ambiguous.

## When queries fail

Use this decision order:

1. Confirm the backend plugin is importable for the URI scheme.
2. Confirm the table exists with `db.show("Table")` or the backend's table-listing method.
3. Confirm field names and datatypes match the inserted documents/schema.
4. Confirm filters/operators are supported by the selected backend.
5. If the failure involves listener outputs or vector similarity, route to the owning sibling sub-skill instead of treating it as a plain select/insert problem.
