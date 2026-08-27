# Parser API Reference

## When to read

Read this before changing parser signatures, return shapes, registry mappings,
or parser configuration keys.

## Parser data types

The `electricitymap.contrib.types.ParserDataType` enum contains 25 data types.
Most are zone-side and use one `zone_key`; exchange-side data types use two zone
keys and are grouped in `EXCHANGE_DATA_TYPES`.

Zone-side examples:

- `production`, `consumption`, `price`, `priceIntraday`
- `generationForecast`, `consumptionForecast`
- `productionPerModeForecast`, `productionPerModeForecastDayAhead`,
  `productionPerModeForecastIntraday`, `productionPerModeForecastLatest`
- `dayaheadLocationalMarginalPrice`, `realtimeLocationalMarginalPrice`
- `gridAlerts`, `intradayContractStatistics`

Exchange-side examples:

- `exchange`, `exchangeForecast`
- `exchangeCapacityForecastDayAhead`, `exchangeCapacityForecastWeekAhead`,
  `exchangeCapacityForecastMonthAhead`
- `atcDayAhead`, `maxBexDayAhead`, `scheduledExchangesDayAhead`,
  `scheduledExchangesTotal`, `maxBflowDayAhead`

`productionCapacity` is in the enum but belongs to the capacity workflow because
its parser signature and side effects differ from live parser smoke checks.

## Function signatures

Native interface tests expect these argument names. Decorators may wrap a
function, but the undecorated function must still match.

```python
# Zone-side parser signature.
def fetch_production(
    zone_key,
    session,
    target_datetime,
    logger,
) -> list[dict] | dict:
    ...

# Exchange-side parser signature.
def fetch_exchange(
    zone_key1,
    zone_key2,
    session,
    target_datetime,
    logger,
) -> list[dict] | dict:
    ...
```

Common default conventions in existing parsers are `session: requests.Session |
None = None`, `target_datetime: datetime | None = None`, and a module logger.
When historical data is unsupported, raise a clear exception rather than
returning misleading latest data for a requested past date.

## Registry and config mapping

The parser registry is built from `CONFIG_MODEL.zones`,
`CONFIG_MODEL.exchanges`, and `PARSER_DATA_TYPE_TO_DICT`:

- Zone config parser mappings look like `production: FR.fetch_production`.
- Exchange config parser mappings look like `exchange: ENTSOE.fetch_exchange`.
- For non-capacity parsers, config model lazy loading expects a top-level
  `parsers.<MODULE>.<FUNCTION>` namespace in some paths.
- The registry module loads concrete functions through
  `electricitymap.contrib.parsers.<MODULE>` for live parsers and
  `electricitymap.contrib.capacity_parsers.<MODULE>` for capacity parsers.

If `CONFIG_MODEL.zones[zone].parsers.get_function("production")` fails with
`No module named 'parsers'`, use the root environment diagnostic or pass
`--repo-root` to the bundled parser helper.

## Output requirements

The parser smoke CLI and native tests enforce these basics:

- Return a truthy dict/list. `None`, `[]`, or `False` is treated as no data.
- Every event must include `datetime` as a native `datetime.datetime` object.
- Datetimes must be timezone-aware.
- Use `zoneKey` for zone-side events and source fields that match the event
  helper model.
- Consumption and exchange outputs are further validated by quality helpers.

Prefer event-list helpers from `electricitymap.contrib.lib.models.event_lists`:

| Event-list helper | Typical parser |
| --- | --- |
| `ProductionBreakdownList`, `TotalProductionList` | production and generation-derived outputs |
| `TotalConsumptionList` | consumption |
| `ExchangeList`, `ForecastTransferCapacityList` | exchange and exchange capacity/forecast outputs |
| `PriceList` | price |

For production parsers, use `ProductionMix` and `StorageMix` from the event
models. The example parser documents an important convention: when a production
mode is missing from the source, omit it or return `None`; do not encode missing
source data as `0` unless the source explicitly reports zero.

## Modes and decorators

`ProductionModes` values are `biomass`, `coal`, `gas`, `geothermal`, `hydro`,
`nuclear`, `oil`, `solar`, `wind`, and `unknown`.

`StorageModes` values are `battery` and `hydro`; storage config/output keys may
surface as `battery storage` and `hydro storage` in capacity/config contexts.

Useful parser decorators/helpers:

- `refetch_frequency(timedelta(...))` annotates a parser with a refetch cadence.
- `retry_policy(Retry(...))` mounts a temporary HTTP retry adapter on the
  supplied session.
- `use_proxy(country_code, monkeypatch_for_pydataxm=False)` uses Webshare
  proxy credentials from `WEBSHARE_USERNAME` and `WEBSHARE_PASSWORD` as a last
  resort.
- `get_token("TOKEN_NAME")` reads environment variables and emits a wiki-style
  token guidance URL when missing.

## Common token variables

Live parser tests often mock these, but live runs may require real values:
`ENTSOE_TOKEN`, `EIA_KEY`, `ESIOS_TOKEN`, `OPENELECTRICITY_TOKEN`,
`RESEAUX_ENERGIES_TOKEN`, `EMAPS_NORDPOOL_USERNAME`,
`EMAPS_NORDPOOL_PASSWORD`, `ERCOT_API_SUBSCRIPTION_KEY`, `ERCOT_API_USERNAME`,
`ERCOT_API_PASSWORD`, `NED_TOKEN`, `JAO_AUCTION_API_KEY`, `MAILGUN_TOKEN`,
`TR_USERNAME`, `TR_PASSWORD`, and Webshare proxy credentials.
