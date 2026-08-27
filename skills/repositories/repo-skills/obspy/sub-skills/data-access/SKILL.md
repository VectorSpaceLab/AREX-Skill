---
name: data-access
description: "This skill guides bounded retrieval of ObsPy waveforms, station
  metadata, and events from FDSN, routing, local SDS/TSIndex, and SeedLink
  services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ObsPy data access

Use this skill when a task must **locate and retrieve** seismic waveforms,
station metadata, or event catalogs. It covers FDSN queries, FDSN routing,
local SDS/TSIndex archives, and live SeedLink streams. It does not process
waveforms, serialize event/inventory objects, or run signal algorithms; route
those tasks to the corresponding sibling skills.

## Safe access contract

1. Turn the request into a data type, exact UTC start/end, network/station/
   location/channel (NSLC) selectors, provider/archive, and a result bound.
   Reject `endtime <= starttime`. Keep empty location codes distinct from
   wildcards.
2. Prefer a **plan before dispatch**. Run the bundled planner with `--help`
   or `--self-test`, then inspect its JSON. It performs no HTTP, SeedLink, or
   file writes. See [query recipes](references/query-recipes.md).
3. Keep requests small and reproducible: use explicit UTC bounds, narrow
   wildcards, one provider where known, a finite timeout, and `filename` only
   when raw server output is deliberately required. Do not add credentials to
   a query plan or log.
4. Dispatch only after the plan is approved. Validate the returned object,
   trace IDs, requested time window, gaps/overlaps, sample rates, and the
   service/archive that was actually used. An empty `Stream`, `Inventory`, or
   `Catalog` is a data result to report, not permission to broaden the query.

## Choose an access path

- **FDSN:** `obspy.clients.fdsn.Client` is the default for ordinary waveform,
  station, and event requests. `get_waveforms()` returns a `Stream`,
  `get_stations()` returns an `Inventory`, and `get_events()` returns a
  `Catalog`. Use `level="response"` only when response metadata is needed.
  FDSN selectors support comma-separated values and `*`/`?` wildcards; use
  `--` for a blank location in a textual plan or query representation.
- **FDSN routing:** `RoutingClient("earthscope-federator")` or
  `RoutingClient("eida-routing")` can route waveform/station requests across
  providers. It does not provide `get_events()`. Its `filename` and
  `attach_response` options are not supported; use direct FDSN clients when
  those are required. Include/exclude providers and a timeout when the
  routing service is appropriate.
- **SDS:** `obspy.clients.filesystem.sds.Client(<archive-root>)` reads the local
  SDS layout. Call `get_waveforms()` with UTC bounds; the client checks nearby
  day files using its border settings. Missing day files are gaps, not a
  reason to contact a remote service. Use `get_availability_percentage()` or
  `Stream.get_gaps()` before handing data to processing.
- **TSIndex:** `obspy.clients.filesystem.tsindex.Client(<database>,
  datapath_replace=(<indexed-prefix>, <local-prefix>))` reads an existing local
  SQLite TSIndex. Use `get_availability_extent()`, `get_availability()`, or
  `has_data()` before `get_waveforms()`. Keep the index and data path local;
  there is no implicit FDSN fallback. `Indexer` is an archive-preparation
  operation and is outside a read-only retrieval plan unless explicitly
  requested.
- **SeedLink:** For approved live streaming, construct
  `EasySeedLinkClient(<host>:<port>, autoconnect=False)`, explicitly connect,
  select streams with `select_stream(network, station, "EH?")`, then run with
  an `on_data(trace)` callback. `run()` is an unbounded loop; define external
  stop/close ownership before using it. `create_client()` connects immediately
  and is therefore not a planning primitive.

## Minimal validation

For waveforms, check `len(stream)`, each `trace.id`, start/end, and
`stream.get_gaps()`; preserve separate traces when gaps matter. For SDS and
TSIndex, compare the requested interval with availability APIs and distinguish
missing archive files from a provider `204`/no-data response. For station and
event results, check object counts and the time/location filters before routing
metadata or serialization work elsewhere. Use the exact service exceptions
(`FDSNNoDataException`, timeout, authentication, request-too-large, or
service-unavailable variants) in troubleshooting rather than retrying every
failure.

## Bundled helper

Use the self-contained planner from a shell or Python environment:

```bash
python scripts/query_plan.py --help
python scripts/query_plan.py --self-test
python scripts/query_plan.py fdsn --service waveforms --base-url https://example.invalid \
  --network IU --station 'A*' --location '' --channel 'BH?' \
  --start 2020-01-01T00:00:00Z --end 2020-01-01T00:10:00Z
```

The helper emits deterministic JSON, never dispatches a request, and marks
local missing files without attempting network recovery. Replace the example
endpoint with a provider selected by the user; `example.invalid` is only a
non-routable planning fixture.

Read [api-reference.md](references/api-reference.md) for signatures and
return contracts, [query-recipes.md](references/query-recipes.md) for bounded
FDSN/routing/SDS/TSIndex/SeedLink recipes, and
[troubleshooting.md](references/troubleshooting.md) for failure handling.
