# Database Recipes

## Supported BYODB families

| Family | Typical connector / extra | When to use | Notes |
| --- | --- | --- | --- |
| SQLite | `sqlite3` from the standard library | local smoke, tests, quick prototypes | no extra needed |
| PostgreSQL | `psycopg[binary]` or SQLAlchemy-backed sessions | server-backed PostgreSQL memory stores | use a normal connection factory or session |
| MySQL | `pymysql` or SQLAlchemy-backed sessions | MySQL-compatible databases | install the driver that matches your stack |
| TiDB | `pymysql` + `memori[tidb-zero]` for provisioning | TiDB-compatible MySQL flows | TiDB Zero provisioning is the packaged provisioning route |
| CockroachDB | `psycopg[binary]` + `sqlalchemy-cockroachdb` | CockroachDB-specific BYODB setups | cloud connection-string mode is also supported in the Python package |
| MongoDB | `pymongo` | MongoDB-backed memory stores | use the MongoDB adapter path from the docs/examples |
| Oracle | `oracledb` | Oracle-backed memory stores | requires an Oracle client strategy that fits the environment |
| OceanBase | `pyobvector` or MySQL-style connection path | OceanBase-backed memory stores | follow the docs for the appropriate connector shape |

## Safe local SQLite recipe

```python
import sqlite3
from memori import Memori

mem = Memori(conn=lambda: sqlite3.connect("memori.sqlite"), use_rust_core=False)
mem.attribution(entity_id="user-123", process_id="chat")
mem.config.storage.build()
```

## Practical selection guidance

- Choose SQLite when you need the smallest no-network smoke.
- Choose PostgreSQL or CockroachDB when the app already uses a SQLAlchemy or
  Psycopg stack.
- Choose MySQL or TiDB when the surrounding stack is MySQL-compatible.
- Choose MongoDB, Oracle, or OceanBase only when the user already has those
  services or drivers in place.

## What not to do

- Do not install every database driver just because the repo supports them.
- Do not treat a cloud quickstart as a BYODB recipe.
- Do not omit the schema build step when the user expects tables to exist.
