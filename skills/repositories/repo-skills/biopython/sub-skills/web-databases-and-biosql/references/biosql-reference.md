# BioSQL reference

BioSQL is Biopython's optional bridge to a relational database schema for persistent biological sequence storage. It is useful when the user needs a shared relational store, namespace-based sequence databases, or cross-language BioSQL compatibility. It is not required for ordinary parsing, indexing, or conversion of sequence files.

## Scope boundary

Use BioSQL only when the task explicitly needs a database-backed sequence store. Otherwise:

- Use `SeqIO.parse`, `SeqIO.index`, or `SeqIO.index_db` for file-backed sequence workflows.
- Use `Bio.Entrez`, `Bio.Medline`, `Bio.SwissProt`, `Bio.KEGG`, or `Bio.ExPASy` for retrieval/parsing workflows.
- Do not set up MySQL/PostgreSQL servers as a default skill action.
- Do not run destructive database operations on a user's existing database without an explicit backup/approval plan.

BioSQL schema files and server administration are outside the required base Biopython skill. Treat them as optional inputs supplied by the user or by an approved environment-preparation step.

## Main entry point

```python
from BioSQL import BioSeqDatabase

server = BioSeqDatabase.open_database(driver="sqlite3", db="example.db")
```

`open_database(driver="MySQLdb", **kwargs)` loads an existing BioSQL-style database. Driver modules must implement the Python DB-API. Common connection keywords include:

- `user`
- `password` or `passwd`
- `host`
- `database` or `db`

Biopython normalizes some keyword names depending on the driver.

## Driver matrix

| Driver | Database | Extra dependency | Server required? | Biopython-specific behavior | Use when |
|---|---|---|---|---|---|
| `sqlite3` | SQLite | Python standard library | No external server | Connects to the database filename and enables `PRAGMA foreign_keys = ON` | Local prototypes, small test databases, no credentials |
| `MySQLdb` | MySQL/MariaDB | `mysqlclient`-style DB-API module | Yes | Maps `database` to `db`, maps `password` to `passwd`, sets `sql_mode='ANSI_QUOTES'` | Existing BioSQL MySQL/MariaDB database |
| `mysql.connector` | MySQL/MariaDB | MySQL Connector/Python | Yes | Same MySQL keyword mapping and ANSI quotes; cursors are adapted for connector behavior | Existing MySQL/MariaDB database when `MySQLdb` is unavailable |
| `psycopg2` | PostgreSQL | `psycopg2` | Yes | Maps `db` to `database`; defaults to `template1` if no database is given; may warn about old BioSQL PostgreSQL rules that slow loading | Existing BioSQL PostgreSQL database |
| `pgdb` | PostgreSQL/PyGreSQL | PyGreSQL | Yes | Uses PostgreSQL-style sequence handling; some DB utility methods are incomplete | Legacy environments only |
| `psycopg` | PostgreSQL v1 driver | Unsupported | Yes | Raises `ValueError`; use `psycopg2` instead | Do not use |

Unknown DB-API drivers may import but fall back to generic SQL helpers; verify carefully before relying on them.

## Core object model

`open_database` returns a `DBServer` object:

```python
from BioSQL import BioSeqDatabase

server = BioSeqDatabase.open_database(driver="sqlite3", db="example.db")
try:
    # Existing namespace:
    db = server["namespace_name"]

    # Or create a namespace after the schema exists:
    db = server.new_database("namespace_name", authority="local", description="Example namespace")

    # Load SeqRecord objects from any normal Biopython parser:
    # count = db.load(records)
    server.commit()
finally:
    server.close()
```

Useful `DBServer` operations:

- `server.keys()`, `server.values()`, and `server.items()` iterate namespaces.
- `server.new_database(name, authority=None, description=None)` creates a namespace.
- `del server[name]` removes a namespace and its entries; treat this as destructive.
- `server.load_database_sql(sql_file)` loads a BioSQL schema file into an empty database.
- `server.commit()`, `server.rollback()`, and `server.close()` wrap transaction lifecycle.

A namespace behaves like a BioSQL-backed sequence database. Loading normally consumes `SeqRecord` objects, so parser choice is still controlled by the file-I/O and database parser skills.

## Setup decision tree

1. **Need only a local searchable file cache?** Use `SeqIO.index_db`, not BioSQL.
2. **Need persistent relational schema with BioSQL interoperability?** Use BioSQL.
3. **Need a quick safe prototype?** Use a temporary SQLite database and an explicit schema file if available.
4. **Need production MySQL/PostgreSQL?** Confirm driver installation, credentials, schema version, backup policy, and whether writes are allowed before connecting.
5. **Need to load downloaded records?** Retrieve or parse records first, then load `SeqRecord` objects into BioSQL; keep retrieval and database-write failures separately reportable.

## Verification guidance

For base Biopython skill checks, import-only BioSQL verification is sufficient:

```python
from BioSQL import BioSeqDatabase
assert callable(BioSeqDatabase.open_database)
```

Use actual database verification only when the user approved database setup or provided an existing safe database. For SQLite, prefer a temporary file. For MySQL/PostgreSQL, verify driver import and a read-only connection before schema loading or record writes.

## Common caveats

- Schema loading requires a valid BioSQL SQL schema file for the target database type.
- SQLite is not a substitute for testing MySQL/PostgreSQL-specific permissions, encodings, or sequence behavior.
- PostgreSQL installations with older BioSQL rules may work but warn and load more slowly.
- MySQL connector behavior differs between `MySQLdb` and `mysql.connector`; keep driver choice explicit in reports.
- Loading large sequence collections should be batched with clear commit/rollback boundaries.
