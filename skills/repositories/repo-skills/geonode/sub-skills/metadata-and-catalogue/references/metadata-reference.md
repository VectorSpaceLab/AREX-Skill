# Metadata reference

## Contract and lifecycle

GeoNode 5 uses a JSON Schema-driven metadata engine. The live schema is built
from the configured handler registry and a base resource schema; later handlers
can add or alter fields. Fetch it rather than assuming a local customization.
The normal endpoints are:

| Operation | Request | Expected result |
|---|---|---|
| Discover | `GET /api/v2/metadata/` | JSON containing `schema` and `instance` URL templates |
| Schema | `GET /api/v2/metadata/schema/?lang=en` | JSON Schema object with `properties`; required fields are at the top level |
| Read instance | `GET /api/v2/metadata/instance/<pk>/?lang=en` | JSON instance with handler-specific values |
| Replace | `PUT /api/v2/metadata/instance/<pk>/` | `200` on success, `422` plus `extraErrors` on handler/save/index errors |
| Partial update | `PATCH /api/v2/metadata/instance/<pk>/` | Same response contract; the server merges the submitted fields |
| Sparse value | `PUT /api/v2/metadata/sparse/<pk>/<key>` | `{"value":"..."}`; string/null only, max 1024 chars |
| Sparse read/delete | `GET` / `DELETE` same sparse URL | `200` when present/deleted, `404` when absent, permission-aware |

The manager builds a schema, serializes each property through the handler named
by `geonode:handler`, then runs handler lifecycle hooks. On write it loads
handler context, runs pre-deserialization hooks, updates fields, runs save hooks,
updates the search index, and returns nested errors. A `422` can therefore mean
field deserialization, model persistence, catalogue-related save follow-up, or
indexing failure; inspect the error path and server log before categorizing it.

## Handler and field map

These are stable source-backed roles, not an alternate schema. The actual
property set and values remain deployment-configurable.

| Handler | Fields/role | JSON shape or behavior |
|---|---|---|
| `base` | core `ResourceBase` fields | Strings, nullable strings, ISO date-time, or `{id,label}` relation objects as defined by the live schema |
| `thesaurus` | `tkeywords` | Object keyed by thesaurus identifier; each value is an array of `{id,label}` |
| `hkeyword` | `hkeywords` | Array of strings; empty entries are discarded on write |
| `region` | `regions` | Array of `{id,label}`; write replaces the resource's region set |
| `doi` | `doi` | Nullable string, max length 255, inserted after `edition` |
| `linkedresource` | `linkedresources` | Array of `{id,label}`; write adds requested links and removes non-internal omitted links |
| `contact` | `contacts` | Role-keyed object; role cardinality and requiredness come from `Roles` |
| `sparse` | registered custom fields | Scalar values or JSON-encoded arrays/objects stored in `SparseField` |
| `multilang` | configured `MULTILANG_FIELDS` | Lead text field plus language-suffixed sparse fields; only text fields may be configured |
| `metadata_cleaner` | incoming instance | Sanitizes HTML-like strings and records a metadata error when it changes content |

The base schema includes required annotations for `title`, `abstract`, `date`,
`date_type`, `category`, `language`, and `license` in the stock schema. The
metadata user guide also describes regions and other fields as important. Do
not reject a record solely because a deployment's fetched schema differs or
because the UI's required marker is present: the user guide explicitly notes
that incomplete catalogue records can remain usable.

Examples of server-produced values:

```json
{
  "title": "Coastal habitats",
  "abstract": "Mapped coastal habitat classes.",
  "date_type": "publication",
  "language": "eng",
  "category": {"id": "oceans", "label": "Oceans"},
  "license": {"id": 7, "label": "CC BY 4.0"},
  "regions": [{"id": "12", "label": "Europe"}],
  "hkeywords": ["habitat", "coast"],
  "tkeywords": {
    "inspire_themes": [{"id": ".../habitat", "label": "Habitats"}]
  },
  "contacts": {"owner": {"id": "3", "label": "editor"}}
}
```

Use IDs from autocomplete/schema responses. A label is display context; it is
not a safe substitute for the identifier. Category and license autocomplete
responses use `{id,label}`. Regions, resources, users, groups, hierarchical
keywords, and thesaurus keywords have dedicated autocomplete routes embedded
in the schema.

## Supported metadata formats and mapping

For metadata ingestion through the resource metadata utilities, the supported
XML root local names are:

| Root local name | Interpreted as | Representative mapping |
|---|---|---|
| `MD_Metadata` | ISO metadata | identifier, language, title, abstract, purpose, supplemental information, temporal extent, topic category, keywords/regions, constraints, maintenance frequency, lineage |
| `metadata` | FGDC metadata | dataset ID, citation title/geoform, abstract, purpose, supplemental information, ISO topic-category hint, theme/place keywords, temporal range, use constraints, date |
| `Record` | Dublin Core CSW record | identifier, language, type, subjects, spatial value, temporal/modified date, license, title, abstract |
| `GetRecordByIdResponse` | CSW wrapper | unwrap the first child, then apply the child root rules |

Dates are normalized from common compact, date-only, ISO UTC, trailing-`T`, and
slash-separated forms; an absent date is replaced during parsing by the current
local timezone timestamp. Keywords and regions are returned separately for the
resource update path. `assert_safe_xml` rejects unsafe XML before parsing.

Catalogue output supports Atom, DIF, Dublin Core, ebRIM, FGDC, and ISO format
names through the CSW backend's format map. That is an output/catalogue
capability and must not be confused with the three input roots accepted by the
resource metadata parser. The default generated catalogue template is ISO
19115-oriented. If `metadata_uploaded` and `metadata_uploaded_preserve` are
true, the preserved XML is used instead of generating the default document.

## Localization and multilingual values

Schema labels/descriptions resolve from the label thesaurus first and gettext
fallback second. A field title can be keyed by its explicit `title` text; an
implicit field title can use the property name. Local overrides use a property
name plus `__ovr`; descriptions use `__descr` and `__descr__ovr`. Overrides are
language-specific and should not replace the canonical key.

The configured language is normalized to its two-letter form for multilingual
field names. A configured text field such as `title` produces names such as
`title_multilang_en` and `title_multilang_it`. The default-language localized
value is copied back into the base field on write. API serializers return the
requested language; add `include_i18n=true` where supported to expose all
prefetched localized values. ISO templates use `LANGUAGE_MAPPINGS` to turn
2-letter codes into ISO 639-2 codes; missing mappings are skipped or fall back
with a warning, not silently invented.

The schema cache is keyed by language and invalidated using the date of the
well-known labels thesaurus. After editing labels, verify the thesaurus date,
force/allow cache refresh, fetch the schema again, and compare the localized
annotation before blaming the client.

## Validation examples

Syntax-only local checks:

```text
python scripts/validate-metadata.py record.xml
python scripts/validate-metadata.py instance.json --required-field title --required-field abstract
```

The helper accepts a caller-supplied required-field list and does not claim full
ISO/FGDC/Dublin Core or JSON Schema conformance. For an XML field check, use the
local XML element name (for example `--required-field title`); namespaces are
ignored for this small check. For JSON, fields are top-level keys. Use the live
schema for type, format, cardinality, relation IDs, and conditional semantics.
