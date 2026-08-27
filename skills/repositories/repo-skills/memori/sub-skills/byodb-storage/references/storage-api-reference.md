# Storage API Reference

## Primary entry point

```python
Memori(conn=..., debug_truncate=True, *, api_key=None, base_url=None, use_rust_core=None)
```

Supplying `conn` switches Memori into BYODB mode. Without `conn`, Memori uses
cloud mode and expects `MEMORI_API_KEY`.

## Supported connection shapes

The storage registry accepts:

- A connection factory `() -> connection`.
- A connection object with `.cursor()`, `.commit()`, and `.rollback()`.
- A SQLAlchemy `Session` object.
- A context-manager style connection that can be entered and later released.

## Build semantics

- `mem.config.storage.build()` creates or upgrades the schema when a connection
  factory is present.
- Schema creation is idempotent for a configured database and is the normal
  follow-up step after constructing a BYODB instance.
- `build()` is the right place to detect missing tables or missing driver setup
  before a user script proceeds to recall or agent capture.

## Dialect families

The Python storage registry recognizes these dialect families:

- `sqlite`
- `postgresql`
- `mysql`
- `tidb`
- `oceanbase`
- `oracle`

TiDB is detected through MySQL-style connectors when the server version reports
TiDB. OceanBase is handled through its dedicated adapter family or its MySQL-
style route depending on the connector type.

## Practical rule

If a user already has a SQLAlchemy `Session`, pass it directly. If they have a
DB-API connection or a small connection factory, pass that instead. Pick the
smallest supported shape that matches the surrounding application.
