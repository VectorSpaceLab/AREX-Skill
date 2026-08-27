# Configuration Models

## When to read

Read this before editing zone/exchange YAML, data-center JSON, co2eq/emission
factor config, parser mappings, or geo-linked zone data.

## Config loading

The package reads static config from the repository `config/` tree:

- `config/zones/*.yaml` becomes `ZONES_CONFIG` and `CONFIG_MODEL.zones`.
- `config/exchanges/*.yaml` becomes `EXCHANGES_CONFIG` and
  `CONFIG_MODEL.exchanges`; filenames use `_`, in-memory keys use `->`.
- `config/data_centers/data_centers.json` becomes `DATA_CENTERS_CONFIG`.
- `config/defaults.yaml` feeds direct and lifecycle co2eq/emission-factor
  models.

Useful imported objects:

- `CONFIG_MODEL`: pydantic model containing `zones` and `exchanges`.
- `CO2EQ_CONFIG_MODEL`: direct and lifecycle co2eq model pair.
- `ZONE_PARENT`, `ZONE_NEIGHBOURS`, `ALL_NEIGHBOURS`: generated maps from zone
  hierarchy and exchange config.
- `emission_factors(zone_key)`: returns the merged latest emission-factor values
  for a zone.

## Zone model fields

The `Zone` model forbids unexpected fields. Common YAML fields include:

- `bounding_box`, `center_point`, `centroid`
- `contributors`, `sources`, comments/URLs through alias-compatible fields
- `parsers` mapping data types to `MODULE.function`
- `capacity` using the capacity model and timeline formats
- `delays`, `generation_only`, `can_have_zero_production`
- `subZoneNames`, `bypassedSubZones`
- `timezone`, `country`, `region`, `currency`
- `zone_name`, `zone_short_name`, `country_name`
- price/license flags such as `has_day_ahead_price_license` and
  `hide_day_ahead_price`

`currency` must be a valid ISO 4217 code when present.

## Parser mappings inside config

Zone parser mappings are validated against `ParserDataType` and the `Parsers`
model. Exchange parser mappings are validated by `ExchangeParsers`. If you add a
new parser data type, update the enum, model fields, and tests together.

Examples:

```yaml
parsers:
  production: FR.fetch_production
  consumption: FR.fetch_consumption
  productionCapacity: ENTSOE.fetch_production_capacity
```

`productionCapacity` routes to the capacity sub-skill; other parser mappings
route to the parser sub-skill.

## Exchange model fields

Exchange configs are lighter:

- `capacity`: tuple-like import/export capacity when known.
- `lonlat`, `rotation`: map rendering metadata.
- `parsers`: exchange-side parser mappings such as `exchange`,
  `exchangeForecast`, `atcDayAhead`, and scheduled/max flow/capacity variants.
- comments through alias-compatible fields.

Filename rules are enforced by the bundled validator: uppercase zone keys and
sorted exchange filename parts.

## Data centers

Data centers are loaded from `config/data_centers/data_centers.json` into the
`DataCenters` model. Treat duplicate IDs, malformed region/zone references, and
missing required fields as model validation errors; run the data-center model
test after edits.

## Co2eq and emission-factor sources

The config model builds direct and lifecycle co2eq parameter models from
`defaults.yaml` plus zone overrides. Tests require zone-specific source labels
to be either known global references or listed under the zone's `sources` map,
except for documented assumptions and Electricity Maps internal references.

When adding emission-factor data:

1. Use direct or lifecycle context deliberately.
2. Include a source label/date/value where the schema expects it.
3. Add or reuse the source in the zone's `sources` map unless it is a global
   reference accepted by tests.
4. Run emission-factor and co2eq tests.

## Geo and hierarchy consistency

`tests/test_zones_json.py` checks bounding boxes, `subZoneNames`, and that every
zone in `geo/world.geojson` exists in `config/zones`. `generate_zone_neighbours`
uses exchange configs and skips exchanges without an `exchange` parser when
building the flow-tracing neighbor graph.
