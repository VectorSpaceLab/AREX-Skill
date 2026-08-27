---
name: metadata-and-catalogue
description: "Operate GeoNode metadata schemas, handlers, localization,
  catalogue/CSW publication, search filters, facets, and metadata-adjacent
  preview context without confusing data validation with service availability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Metadata and catalogue

Use this sub-skill when a task edits, validates, localizes, indexes, searches, or
publishes resource metadata, or when a catalogue/search result does not match
expectations. It covers datasets and other `ResourceBase` resources. Route
upload mechanics and ordinary resource CRUD to `resource-and-api`; route
GeoServer publication, service URLs, styles, and permissions to
`geoserver-and-security`; route remote harvesting and worker recovery to
`harvesting-and-admin`.

## Operating boundary

- Treat the metadata JSON Schema as the authoritative shape for the metadata
  editor/API instance. Do not invent a replacement ISO, FGDC, or Dublin Core
  schema.
- Treat the configured catalogue backend and its URL as separate service
  dependencies. A valid local document does not prove CSW availability.
- Treat required metadata annotations as editor guidance unless the active
  deployment adds a separate policy gate: the user guide says incomplete
  metadata remains usable.
- Never send credentials, mutate a remote catalogue, or run a network CSW
  helper from the bundled validator.
- External PostgreSQL/PostGIS, GeoServer, Redis/Celery, remote CSW/OGC
  endpoints, and browser services are prerequisites for corresponding live
  workflows and are not verified by this skill.

## Route the request

1. Identify the resource primary key or UUID and whether the request is about
   schema, one resource instance, XML import/export, catalogue transport,
   search, facets, or preview/style context.
2. For schema/instance work, read [metadata-reference.md](references/metadata-reference.md).
3. For CSW, OpenSearch, catalogue links, full-text search, or facets, read
   [catalogue-and-search.md](references/catalogue-and-search.md).
4. For a supplied local JSON/XML file, run `scripts/validate-metadata.py` first;
   use explicit required fields when a deployment or task supplies them.
5. If the validator passes but a catalogue request fails, switch to the
   service-gate diagnosis in [troubleshooting.md](references/troubleshooting.md)
   rather than changing the metadata blindly.

## Metadata API workflow

- Discover the metadata endpoints from the API base: `GET
  /api/v2/metadata/` returns schema and instance URL templates.
- Fetch the localized schema with `GET /api/v2/metadata/schema/?lang=<2-letter>`.
  Record the returned `properties`, top-level `required`, each
  `geonode:handler`, and any autocomplete URL before constructing a payload.
- Fetch an instance with `GET /api/v2/metadata/instance/<pk>/?lang=<lang>`.
  Preserve object/array shapes and IDs returned by the server.
- Use `PUT` for a complete instance or `PATCH` for selected fields. A successful
  update returns HTTP 200; handler/save/index errors return HTTP 422 with
  `message` and nested `extraErrors`. A missing resource is HTTP 404.
- After saving, verify the response, re-fetch the instance, and check search or
  CSW only after the indexing/catalogue gates are known.
- For a declared custom field, use the sparse endpoint only when it is absent
  from the declared schema: `PUT /api/v2/metadata/sparse/<pk>/<key>` with
  `{"value":"..."}`. Values are strings or null and are limited to 1024
  characters; schema-name collisions return HTTP 409.

## Metadata, search, and preview handoff

- The default schema is ISO-19115-oriented and includes fields such as title,
  abstract, date/date type, category, language, license, attribution, regions,
  keywords, restrictions, temporal extent, maintenance frequency, and spatial
  representation. Exact type/cardinality comes from the live schema.
- Metadata values also feed generated ISO XML, catalogue `AnyText`, resource
  indexes, resource information pages, relations, and discoverability. A
  thumbnail, map preview, or style is publication/visual context, not a
  substitute for title, abstract, extent, or keyword metadata.
- For a styled dataset, verify the resource subtype and GeoServer/style gate
  separately. Keep metadata diagnosis focused on fields and catalogue/index
  state.

## Verify and recover

- Validate local syntax and explicit fields before import. Keep the validator's
  exit status and messages with the task record.
- Compare schema, submitted instance, saved instance, generated metadata XML,
  `csw_anytext`, and search/index results in that order.
- On a failed update, use `extraErrors` to locate the field/handler; correct the
  payload and retry without resending unrelated fields.
- On stale discovery, check index freshness and catalogue regeneration rather
  than declaring the source invalid. Use a deployment-approved regeneration
  command with a dry run or narrow ID filter before broad changes.
- Report unverified service gates explicitly. See
  [troubleshooting.md](references/troubleshooting.md) for symptom-specific
  next steps and [catalogue-and-search.md](references/catalogue-and-search.md)
  for filter semantics.

## References and helper

- [Metadata reference](references/metadata-reference.md): handlers, field
  mappings, localization, schemas, instances, and examples.
- [Catalogue and search](references/catalogue-and-search.md): CSW backends,
  format roles, indexes, facets, filters, and preview boundary.
- [Troubleshooting](references/troubleshooting.md): owned failure modes and
  safe recovery decisions.
- `scripts/validate-metadata.py`: local-only XML/JSON syntax and caller-supplied
  required-field checker. It does not contact a catalogue or validate against a
  remote standards service.
