# Backup, restore, and upgrade

PyCaret platform state has two durable layers:

1. Metadata database: users, workspaces, experiments, runs, jobs, schedules,
   registry rows, deployments, secrets ciphertext, and lineage.
2. Object/artifact storage: uploaded datasets, pickles, run notebooks, plots,
   batch predictions, and registry artifacts.

Back up both. A DB dump without matching artifacts leaves metadata pointing at
missing objects; artifacts without a DB dump are difficult to reconstruct.

## Pre-change checklist

Before a migration, image upgrade, restore, or key rotation:

```bash
pycaret-server doctor
python scripts/ops_doctor.py
bash scripts/check_container_secret_key.sh --data-dir ./data
```

Record:

- application and image versions,
- `PYCARET_DATABASE_URL` backend type,
- `PYCARET_STORAGE_BACKEND`, bucket/endpoint or local artifact root,
- whether `PYCARET_RUNS_BACKEND=redis`,
- worker queue list,
- whether the Fernet key is environment-injected or container-persisted.

Never print the Fernet key, JWT secret, storage secrets, or DB password in the
runbook.

## Database backups

### Postgres

Use native Postgres backup tooling for production-shaped deployments:

```bash
# Compose example.
docker exec pycaret-postgres pg_dump -U pycaret pycaret | gzip > pycaret-db.sql.gz

# Kubernetes example shape; adjust resource names to the actual release.
kubectl -n pycaret exec sts/pycaret-postgres -- pg_dump -U pycaret pycaret | gzip > pycaret-db.sql.gz
```

Restore into a fresh database, then run migrations to the expected release:

```bash
gunzip -c pycaret-db.sql.gz | psql "$PYCARET_DATABASE_URL"
pycaret-server migrate
pycaret-server doctor
```

For managed Postgres, prefer provider snapshots plus periodic logical dumps.
Test restores quarterly.

### SQLite

SQLite is suitable for single-process or compact local installs. For a
consistent backup, stop the API or ensure no writes are in progress, then copy
both DB and artifacts:

```bash
# stop service first when possible
cp ./data/pycaret.db ./backup/pycaret.db
rsync -a ./data/artifacts/ ./backup/artifacts/
```

In compact Docker Compose, the DB, local artifacts, and persisted Fernet key all
live in the named data volume. Back up that volume as a unit or bind-mount data
to a host directory and copy it while the service is stopped.

## Object-store backups

### Local filesystem

```bash
rsync -a ./data/artifacts/ ./backup/artifacts/
```

### MinIO or S3

```bash
mc alias set source http://minio:9000 "$PYCARET_STORAGE_ACCESS_KEY" "$PYCARET_STORAGE_SECRET_KEY"
mc mirror source/pycaret-artifacts ./backup/artifacts

# For AWS S3.
aws s3 sync s3://pycaret-artifacts ./backup/artifacts
```

Take the DB dump first, then mirror the object store. If a DB row references a
new object that has not synced yet, a later mirror can backfill it. The reverse
order can produce DB rows pointing at objects that were never captured.

## API backup and restore endpoints

The API includes superuser-only endpoints:

- `GET /api/v1/admin/backup` streams a tarball containing `database.json` and
  files from the configured local artifact directory.
- `POST /api/v1/admin/restore` accepts a backup tarball and refuses to overwrite
  existing data unless `confirm=true` is supplied.

Use these endpoints for small/local state capture or emergency inspection. They
are not a replacement for native Postgres dumps and S3/MinIO backups in a
production-shaped deployment, because the endpoint implementation packages the
local artifact directory rather than walking every external object-store object.

Restore safety:

```bash
# Shape only; pass auth headers and multipart form fields as required.
curl -H "Authorization: Bearer $TOKEN" \
  -o pycaret-backup.tar.gz \
  http://localhost:8020/api/v1/admin/backup

curl -H "Authorization: Bearer $TOKEN" \
  -F "file=@pycaret-backup.tar.gz" \
  -F "confirm=true" \
  http://localhost:8020/api/v1/admin/restore
```

After restore, run `pycaret-server migrate`, `pycaret-server doctor`, and a UI
smoke test.

## Migrations

Primary command:

```bash
pycaret-server migrate --revision head
```

Useful variants:

```bash
# Explicit DB URL.
pycaret-server migrate --url 'postgresql+psycopg://user:password@host:5432/pycaret'

# Destructive local SQLite reset only; refuses non-SQLite URLs.
pycaret-server migrate --reset-dev
```

Startup behavior:

- SQLite dev databases can auto-apply Alembic migrations on app startup.
- Non-SQLite production databases should be migrated explicitly before the API
  starts against a new schema.
- Empty non-SQLite DBs without explicit migration should fail loudly rather
  than silently creating a schema.

## Upgrade runbook

1. Read release notes for migration and breaking-change notes.
2. Stop or drain workers. Let in-flight runs finish when possible.
3. Back up DB and object storage, and confirm the Fernet key is preserved.
4. Pull/build the new API and web images or install the new package version.
5. Run `pycaret-server migrate` against the production DB.
6. Start/roll the API.
7. Start/roll workers with the correct queues.
8. Run:
   ```bash
   pycaret-server doctor
   python scripts/ops_doctor.py
   curl -f http://localhost:8020/healthz
   ```
9. Smoke test setup/login, workspace list, a small run, queue admin, and one
   artifact download or prediction path.

## Rollback

- Roll image/package versions back first.
- If the DB schema changed, use an Alembic downgrade only if the migration for
  that release explicitly supports it and after restoring a backup if needed.
- Restore DB and object storage from the same backup window.
- Restore the same Fernet key that encrypted stored secrets.
- Run doctor and a UI/API smoke test before reopening traffic.

## Smoke checks after backup/restore/upgrade

```bash
pycaret-server doctor
python scripts/ops_doctor.py --json
curl -f http://localhost:8020/healthz
```

Authenticated API checks:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8020/api/v1/workspaces
curl -H "Authorization: Bearer $TOKEN" http://localhost:8020/api/v1/admin/queues
curl -H "Authorization: Bearer $TOKEN" http://localhost:8020/api/v1/admin/system
```

Expected healthy signs:

- DB check succeeds.
- Redis is `SKIP` for `inprocess` or `OK` for `redis`.
- Storage backend can be reached or the local artifact directory exists and is
  accessible.
- Queue list matches worker deployment intent.
- No decrypt errors appear when reading stored secrets or configured
  connections.
