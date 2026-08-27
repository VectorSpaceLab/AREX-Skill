# Models, Stores, and Migrations

## Layer Map

ZenML server/store work usually crosses multiple layers. Do not change only the file where the failing assertion appears.

- Domain models: request, update, response body/metadata/resources, response, and filter classes under the shared model layer.
- REST routers: FastAPI endpoints that validate, authorize, call feature gates, and delegate to store methods.
- Store interfaces: abstract method contracts and method names used by SQL, REST, and resource-specific store adapters.
- REST store: client-side implementation that serializes filters and requests to server routes and validates response models.
- SQL store: database-backed implementation that queries SQLModel schemas and converts schemas to response models.
- SQLModel schemas: table definitions, relationships, indexes, conversion helpers, and update logic.
- Alembic migrations: schema/data upgrade files required for SQLModel changes.
- Client/CLI/docs: user-facing surfaces that must follow filter and endpoint contract changes; route those details to `../cli-and-client/SKILL.md` when needed.

## Domain Model Pattern

Model families use a layered Pydantic v2 structure.

- Request models create entities and should inherit the narrowest correct scope (`BaseRequest`, `UserScopedRequest`, or `ProjectScopedRequest`).
- Update models inherit `BaseUpdate`, make mutable fields optional, and omit immutable entities.
- Response models split fields into Body, Metadata, and Resources; convenience properties read from `get_body()`, `get_metadata()`, or `get_resources()`.
- Hydrated-only data belongs in metadata/resources and should be loaded through `get_hydrated_version()` or explicit `hydrate=True` store calls.
- Filter models inherit the matching scoped filter base and use typed filter options for strings, UUIDs, datetimes, enums, and numerics.
- Use Pydantic `Field` titles/descriptions and validators to encode API semantics, length limits, and non-empty resource dictionaries.

When adding a filter field, update the filter model, the Python Client method signature, and CLI/list options that pass keyword arguments. Relationship-backed filters may also need custom SQL joins or denormalized columns.

## SQLModel Schema Pattern

SQL schemas should mirror the domain model exactly enough that conversion is predictable.

- Inherit `BaseSchema` or `NamedSchema`; set a singular `__tablename__`.
- Use `build_foreign_key_field` for foreign keys and keep `back_populates` relationships symmetric.
- Use association/link schemas for many-to-many relationships, usually with composite primary keys and cascade delete where appropriate.
- Add explicit unique constraints and indexes for names, hot filters, pagination, queue scans, and denormalized fields.
- Keep external string identifiers under the repository's string length limits unless there is a documented reason for a larger text column.
- Implement or update `from_request`, `update`, `to_model`, `get_query_options`, and resource/metadata loading behavior together.
- For JSON/base64/config fields, keep encoding and decoding symmetric and test both request-to-schema and schema-to-model paths.

## Store Contract Pattern

Every new persisted capability needs coherent store coverage.

- Add abstract methods to the relevant store interface with precise request/update/filter/response types.
- Add SQL implementation using sessions, schema conversion, scoping, pagination, and hydration conventions from neighboring entities.
- Add REST store implementation with the matching HTTP method, path, request body, query filters, hydration flag, and response model.
- Add server router methods that call `zen_store().method_name` or the relevant specialized store interface.
- Add tests for create/get/list/update/delete behavior, filter behavior, hydration behavior, and not-found/conflict cases.

Resource pools use a specialized store interface with pool, subject-policy, and resource-request methods. Keep resource allocation, queue, policy, and request status semantics together; changing only a response model can break scheduling behavior.

## Trigger Update Matrix

Trigger changes are cross-layer by design.

- Domain models include base trigger contracts, schedule/platform-event specializations, dispatch status/error state, filter fields, and type/flavor unions.
- Registry mappings connect trigger types/flavors to concrete request, update, response body, and response classes.
- SQL schemas persist base fields, JSON configuration, denormalized filter columns such as next occurrence or source entity, snapshot associations, execution links, and latest-run lookup behavior.
- Routers apply schedule feature gates, validate source-entity permissions, and handle attach/detach/dispatch operations that span triggers, snapshots, and pipeline runs.
- Store methods must maintain trigger-snapshot dispatch state, trigger executions, archived behavior, latest-run semantics, and filter joins.
- Client/CLI surfaces expose trigger creation/update/listing and must be kept compatible when filter or request fields change.

Native verification candidates for trigger work include CRUD tests that attach triggers to snapshots, create trigger executions, filter pipeline runs by trigger ID, and assert latest-run behavior.

## Resource Pool Update Matrix

Resource pools coordinate API models, queue/allocation schemas, policies, resource requests, stores, and server endpoints.

- Pool requests require non-empty positive capacities; updates may use non-negative values where zero removes a resource.
- Pool responses expose capacity, occupied resources, queue length, active allocations, and queued requests.
- Resource requests include component ID, step run ID, requested resources, status, status reason, preemptibility, and optional related resources.
- Schemas include pool, pool resource, queue, allocation, policy, and request tables with uniqueness and queue-oriented indexes.
- Endpoints are feature-gated and RBAC-protected; list endpoints use dependable filters.
- Store interfaces expose pool CRUD, policy CRUD, request list/get/delete, and SQL-only allocation/release methods.
- Scheduling/backend behavior can depend on queue priority, claim expiration, occupied resources, and release semantics; update tests around allocation and cleanup when changing these fields.

## Migration Rules

SQLModel schema changes usually require an Alembic migration.

- Create a new revision with a descriptive message; do not modify historical migrations that are already on the primary development branch.
- Review autogenerated migrations manually. Alembic cannot safely infer renames, required field backfills, JSON transformations, or MySQL-specific constraints.
- Include data migrations when adding required columns or changing serialized structures used by existing rows.
- Consider SQLite and MySQL differences, especially column types, indexes, constraints, batch operations, and foreign-key behavior.
- Test upgrades from a populated database representing the previous version, not only from an empty database.
- Run the bundled branch checker after rebases or concurrent migration work.
- Coordinate rolling compatibility: old clients may talk to new servers, new clients may see old server responses during deploy, and existing workers may continue writing old payload shapes during the rollout.

## Rolling Compatibility Checklist

- Prefer additive nullable columns or defaulted fields before enforcing strict required behavior.
- Keep response properties tolerant of absent metadata/resources when older servers do not hydrate a new relationship.
- Keep update models backward-compatible unless a deliberate breaking change is approved.
- Avoid changing enum string values stored in the database; add aliases or migrations if unavoidable.
- Keep REST paths stable and add new query/body fields without changing existing meanings.
- Make migrations idempotent enough for interrupted deployment recovery where Alembic supports it.
