# Upload formats and data assumptions

The importer chooses a handler from the submitted fields, filename, content
validation, and action. A filename alone is not sufficient evidence that the
payload is valid. The server also applies upload size and per-user parallelism
limits before the asynchronous handler pipeline starts.

## Action matrix

| `action` | Input | Target/constraints | Typical result |
|---|---|---|---|
| `upload` (default) | `base_file`, optional XML/SLD | New supported resource; handler must recognize actual content | Async import/publish/create |
| `replace` | `base_file`, `resource_pk` | Existing compatible dataset; vector/raster class must match | Replace underlying data, retain resource identity where supported |
| `upsert` | `base_file`, `resource_pk`, optional `upsert_key` | Experimental vector-only path; same schema/types/CRS and non-null unique key | Update matching rows and insert new rows |
| `create` | `title`, `geom`, `attributes`, no file | Empty vector schema; supported dynamic model types | Async empty dataset creation |
| `resource_style_upload` | SLD file and `resource_pk` | Existing dataset and style permission | Apply style through handler/service |
| `resource_metadata_upload` | XML file and `resource_pk` | Safe supported metadata; matching UUID when present | Apply metadata through handler/service |
| `copy` | Existing resource and copy defaults | View/copy plus add/download permission as appropriate | Async clone with assets/links as supported |

The action is an execution request action, not a promise that a resource is
created synchronously. Poll and inspect the final output.

## Local vector formats

### GeoJSON

Accepted extensions are `.geojson` and `.json`; the content must parse as JSON
with top-level `type` `FeatureCollection` or `Feature`. A malformed JSON file,
a binary/PE-like file renamed `.geojson`, or a filename with extra dots is
rejected. A valid feature collection should provide consistent geometry and
property types, a useful CRS interpretation (GeoJSON commonly uses WGS84),
and at least one feature for upsert.

### ESRI Shapefile

Provide the same basename for required `.shp`, `.shx`, `.dbf`, and `.prj` files;
`.cpg`, `.cst`, XML, and SLD are optional where the handler supports them.
The upload validation checks the actual file signatures/descriptions, not just
extensions. The projection is taken from the projection sidecar when present;
missing or inconsistent sidecars can make import or publication fail.

### GeoPackage

Use a `.gpkg` SQLite/GeoPackage file. The handler validates a usable source and
selected GeoPackage requirements, including at least one feature, consistent
geometry SRID, and supported geometry metadata. A replace/upsert GeoPackage
must contain one layer. Do not send a renamed JSON or arbitrary SQLite file.

### CSV and tabular data

Use `.csv` with a readable header. Geometry can be represented by a recognized
WKT/geometry column or by paired latitude/longitude columns (`lat`/`latitude`/
`y` and `lon`/`long`/`longitude`/`x`). If no geometry indicators exist, GeoNode
may classify the result as tabular. A lone latitude or longitude column is
invalid. Check delimiter, encoding, numeric coordinates, and column names
before upload.

### KML/KMZ, XLSX, and 3D Tiles

KML/KMZ uses XML/ZIP validation and OGR KML support. A KMZ is a zip-based
format and must pass archive safety checks. XLSX support is feature-toggle
controlled; it is converted through the first sheet and requires unique,
non-empty headers with latitude and longitude columns. 3D Tiles uploads and
remote tilesets have their own handler and JSON required keys; they are not
vector datasets and cannot be replace/upsert targets.

### Raster

GeoTIFF extensions include `.tif`, `.tiff`, `.geotif`, and `.geotiff` with an
image/tiff-compatible payload. GDAL must be able to open the raster and derive
a spatial reference for robust publication. Local storage is required for
GeoServer to access uploaded raster data. A vector/raster type mismatch is a
replace error.

## Metadata, styles, and documents

- XML metadata and SLD inputs are parsed as XML and pass an unsafe-XML gate.
  External entities, unsafe declarations, or malformed XML should be rejected
  before processing. Use only a schema-appropriate ISO/FGDC/Dublin Core or SLD
  file for the selected action.
- Documents are uploaded through the document upload workflow with `doc_file`
  or referenced using `doc_url`, never both. The allowed extension is a
  deployment setting. Supported documented families include text, office
  documents, spreadsheets, presentations, images, PDF, archives, SLD, XML,
  QML, and URL references; verify `ALLOWED_DOCUMENT_TYPES` on the site.
- ZIP-based document formats (`zip`, `kmz`, OOXML, ODF) are inspected for
  traversal, symlink entries, entry count, uncompressed size, and suspicious
  compression ratios. XML/SLD document contents receive an unsafe-XML check.

## Remote sources

The remote importer validates the URL against the site's safe-URL policy and
may require an authenticated remote service. Supported source types in this
snapshot include WMS, COG, FlatGeobuf, and 3D Tiles. WMS additionally needs an
`identifier`, may accept a `bbox` and `parse_remote_metadata`, and can reuse a
registered service's auth only under that service's rules. COG and FlatGeobuf
need HTTP range support. 3D Tiles needs a valid JSON tileset with `asset`,
`geometricError`, and `root`, plus safe redirect handling.

A representative WMS payload is:

```json
{
  "title": "Remote roads",
  "url": "https://remote.example/ows",
  "type": "wms",
  "identifier": "workspace:roads",
  "parse_remote_metadata": false,
  "action": "upload"
}
```

Do not put remote usernames/passwords in shell history or status logs. Remote
endpoint DNS, TLS, allowlist, credentials, capabilities, range support, and
GeoServer publication are external gates and must remain unverified unless a
specific isolated service test proves them.

## Archive safety and companion-file rules

Run the bundled archive validator before a ZIP/KMZ/XLSX/OOXML/ODF upload:

```sh
python scripts/validate-upload-archive.py clean.zip
python scripts/validate-upload-archive.py --self-test
```

It reads the central directory without extraction. It rejects absolute paths,
`..` path segments (including Windows separators), NUL names, Unix symlinks,
too many entries, total expansion above 2 GiB, and suspicious per-entry or
aggregate compression ratios. This validator is a preflight aid; the deployed
GeoNode serializer remains authoritative.

Never manually extract an untrusted archive before validation. A shapefile ZIP
still needs the required same-basename components after validation; archive
safety does not establish geospatial correctness.
