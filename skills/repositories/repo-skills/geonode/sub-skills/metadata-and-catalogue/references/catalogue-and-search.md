# Catalogue and search reference

## CSW configuration and endpoint contract

GeoNode exposes the catalogue at `/catalogue/csw` and an OpenSearch
advertisement at `/catalogue/opensearch`. The configured `CATALOGUE.default`
entry selects an engine and a fully-qualified `URL`. The stock default is the
local pycsw backend; HTTP pycsw and generic OWSLib-compatible backends are
available alternatives. The local dispatch applies Django visibility, group,
advertised, and optional resource-type filters before pycsw serves the request.

A catalogue request requires all of the following gates:

1. The web application is reachable at the configured site URL.
2. The catalogue engine is installed and loadable.
3. For local pycsw, the Django database and pycsw repository configuration are
   available; the local path does not require a second HTTP service but still
   requires database state.
4. For HTTP/generic backends, the configured remote CSW URL, network, TLS,
   authentication, and server capabilities are available.
5. A resource save or metadata update has generated/synchronized its metadata
   XML, links, `csw_anytext`, and geometry fields.

Do not claim a CSW outage from malformed source XML, and do not claim valid
metadata from an HTTP 200 alone. Inspect the response content type, CSW
`ExceptionReport`, record count, and `GetRecordById` result.

The standard route names are:

```text
GET /catalogue/csw?service=CSW&version=2.0.2&request=GetCapabilities
GET /catalogue/csw?service=CSW&version=2.0.2&request=GetRecordById&id=<uuid>&outputschema=http://www.isotc211.org/2005/gmd&elementsetname=full
GET /catalogue/csw?service=CSW&version=2.0.2&request=GetRecords&typenames=csw:Record&elementsetname=full&resulttype=results
GET /catalogue/uuid/<uuid>
```

For a remote HTTP backend, record links are generated as `GetRecordById` URLs
for configured format output schemas. A generated record's `metadata` links
and download links are distinct from GeoServer OGC links.

## Field mapping and freshness

The catalogue post-save signal creates or updates the record, retrieves it to
rebuild metadata links, stores the resource bounding WKT, renders the selected
metadata template unless preserved uploaded XML is active, and extracts XML
text into `csw_anytext`. The pycsw local mapping binds core fields such as
`uuid`, `title`, `raw_abstract`, `language`, `date`, `csw_wkt_geometry`,
`temporal_extent_start/end`, `restriction_code`, `raw_constraints_other`,
`topiccategory`, `download_links`, and `contacts` to pycsw queryables.

Use this freshness ladder:

1. `GET /api/v2/metadata/instance/<pk>/` shows the new value.
2. The resource's generated metadata XML contains the value.
3. `csw_anytext` or the local index contains the normalized text.
4. `GetRecordById` returns the current record.
5. CSW `GetRecords`, OpenSearch, resource API search, and facets show it.

A resource update also calls the metadata index manager. The configured
`METADATA_INDEXES` commonly include `title`, `title_abstract`, and `all`; the
index manager creates language-specific PostgreSQL tsvectors when an indexed
field is multilingual and a nonlocalized vector otherwise. It fills missing
localized title entries with available title text to preserve discoverability.
PostgreSQL full-text search is a service/backend gate; a Python import is not an
index verification.

## Resource search and filters

The resource API uses dynamic filters and a visibility-aware queryset. Useful
semantics include:

| Request parameter | Meaning |
|---|---|
| `search=<text>` | Full-text search when paired with a configured `search_index` |
| `search_index=title`, `title_abstract`, or configured name | Selects a metadata index; unknown names are validation errors |
| `search_lang=<2-letter>` | Selects a multilingual index language; invalid values fall back to request/default language |
| `search_fields=a&search_fields=b` | Dynamic Django search fields; mutually exclusive with `search_index` |
| `extent=<bbox>` | Spatial bounding-box filter; use the API's documented bbox ordering |
| `filter{tkeywords}=<id>` | Thesaurus keyword filter; default mode requires at least one keyword per thesaurus when multiple IDs are supplied |
| `force_and=true` | Makes multiple thesaurus keyword IDs an all-of intersection |
| `favorite=true` | Restricts to the authenticated user's favorites |
| `advertised=true/false/all` | Controls advertised resources; default visibility also depends on user/owner |

The dynamic search filter reads repeated `search_fields`; do not send both
`search_index` and `search_fields`. Search input is sanitized into ordered
prefix tokens by the index filter. Empty search values bypass the index filter.
A matching metadata field but missing/stale index is an index freshness problem.

## Facets

The facet routes are `/api/v2/facets` and `/api/v2/facets/<facet>` (deployment
prefixes may vary). `GET /facets?include_topics=true&lang=en` lists configured
providers and optionally their topics. A single facet accepts `page`,
`page_size`, `lang`, `topic_contains`, repeated `key`, `include_config`, and
`add_links`. Topic payloads have `key`, `label`, `count`, and sometimes
`is_localized`, `fa_class`, `image`, or children.

Stock providers include resource type, featured, category, hierarchical
keyword, region, owner, group, and configured thesauri. Filters are provider
metadata, not universal field names; read each facet's returned `filter` value
and reuse it. Facets prefilter visible resources through the resource API, then
apply other facet filters. Counts must be compared with the same visibility and
advertised settings as the resource list.

A thesaurus topic uses a localized label when present and `alt_label` otherwise.
`key` is provider-specific: category identifier, region code, keyword slug,
owner/group ID, or thesaurus keyword ID. `key` may request zero-count topics so
that selected filters remain visible.

## Styling and preview boundary

Resource information exposes title, abstract, publication date, owner,
category, regions, location/bbox, relations, assets, permissions, and full
metadata. Dataset preview and style editing are viewer/GeoServer concerns.
Metadata may supply title, abstract, keywords, extent, attribution, and links to
make a preview discoverable, but it does not create a style or prove WMS/WFS
availability. Route style validation, legend/WMS failures, thumbnail
rendering, and GeoServer synchronization to the GeoServer sub-skill.
