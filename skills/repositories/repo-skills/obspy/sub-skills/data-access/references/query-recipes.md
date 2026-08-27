# Bounded data-access recipes

All examples use explicit UTC bounds and a finite scope. Replace placeholder
providers and paths only after validating them. None of the planning examples
should be treated as evidence that the endpoint is reachable.

## 1. Plan a wildcard FDSN waveform request

Use the bundled script first:

```bash
python scripts/query_plan.py fdsn --service waveforms \
  --base-url https://example.invalid \
  --network IU --station 'A*' --location '' --channel 'BH?' \
  --start 2020-01-01T00:00:00Z --end 2020-01-01T00:10:00Z
```

The output records an encoded `query_url`, normalized blank location (`--`),
selectors, and no-dispatch status. Validate that the interval is UTC, the
wildcards are intentional, and the duration is within the task budget. To
dispatch using ObsPy after approval:

```python
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

t0 = UTCDateTime("2020-01-01T00:00:00Z")
t1 = UTCDateTime("2020-01-01T00:10:00Z")
client = Client("EARTHSCOPE", timeout=120)
st = client.get_waveforms("IU", "A*", "", "BH?", t0, t1,
                          longestonly=True)
if not st:
    print("No waveform data returned")
else:
    st.sort()
    print(st)
    print("gaps/overlaps:", st.get_gaps())
```

Use `get_waveforms_bulk()` for a finite list of known rows. Avoid an empty
bulk request: ObsPy explicitly rejects it because it could mean all data.

## 2. Query station and event metadata

Station metadata:

```python
inv = client.get_stations(network="IU", station="ANMO", location="00",
                          channel="BH?", starttime=t0, endtime=t1,
                          level="response")
```

Use `level="station"` for availability-oriented metadata and
`level="response"` only when a downstream response operation needs it. For
events, select a provider that exposes an event service:

```python
from obspy.clients.fdsn import Client
cat = Client("ISC", timeout=120).get_events(
    starttime=t0, endtime=t1, minmagnitude=4.0, limit=100,
    orderby="time-asc")
```

Check `len(inv.networks)`, `len(inv)`/channel counts, or `len(cat)` and report
the provider plus filters. Keep serialization in the formats-and-metadata
workflow.

## 3. Route a bounded waveform request

Use routing only when the provider is unknown or data are federated:

```python
from obspy import UTCDateTime
from obspy.clients.fdsn import RoutingClient

router = RoutingClient("earthscope-federator", timeout=120,
                      include_providers=["EARTHSCOPE"])
st = router.get_waveforms(network="IU", station="ANMO", location="00",
                           channel="LHZ",
                           starttime=UTCDateTime("2020-01-01"),
                           endtime=UTCDateTime("2020-01-01T00:05:00"))
```

A routed request can fan out to multiple HTTP services. Limit providers or
use a direct known provider when reproducibility matters. Routing supports
station queries with analogous filters but not events. Do not pass `filename`
or `attach_response` to the routing methods.

## 4. Read SDS with explicit gap policy

```python
from obspy.clients.filesystem.sds import Client

archive = Client("/data/sds", sds_type="D", format="MSEED",
                 fileborder_seconds=30, fileborder_samples=5000)
st = archive.get_waveforms("IU", "ANMO", "", "HHZ", t0, t1,
                           merge=None)
coverage, gaps = archive.get_availability_percentage(
    "IU", "ANMO", "", "HHZ", t0, t1)
print("coverage", coverage, "gaps", gaps)
```

The SDS client checks adjacent day files because records can spill across
midnight. A missing day file remains a local gap; this workflow must not
instantiate an FDSN client as a hidden fallback. If a continuous stream is
required, reject or explicitly document the gap rather than silently filling
it. Use `merge=0` only when a downstream consumer wants merged traces and the
gap/fill policy is known.

For archive inventory, use `has_data()` before an expensive read and
`get_all_nslc()`/`get_all_stations()` for a local availability listing. Keep
scans bounded on network-mounted filesystems.

## 5. Read a TSIndex archive

```python
from obspy.clients.filesystem.tsindex import Client

archive = Client("/data/index/timeseries.sqlite",
                 datapath_replace=("^", "/data/archive/"))
rows = archive.get_availability(
    network="IU", station="ANMO", location="10", channel="BHZ",
    starttime=t0, endtime=t1, include_sample_rate=True,
    merge_overlap=True)
if rows:
    st = archive.get_waveforms("IU", "ANMO", "10", "BHZ", t0, t1)
```

The index can report availability even when indexed paths are stale or absent;
catch local file/read errors and verify returned traces. Do not use an FDSN
fallback without an explicit second plan and approval.

## 6. SeedLink streaming with a bounded owner

SeedLink is live and callback-driven, not a finite retrieval call. Inspect
capabilities and define the stop mechanism outside the client before running:

```python
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient

class Collector(EasySeedLinkClient):
    def __init__(self, *args, max_traces=10, **kwargs):
        self.traces = []
        self.max_traces = max_traces
        super().__init__(*args, **kwargs)
    def on_data(self, trace):
        self.traces.append(trace)
        if len(self.traces) >= self.max_traces:
            self.conn.terminate()

client = Collector("seedlink.example:18000", autoconnect=False)
client.connect()
if client.has_capability("multistation"):
    client.select_stream("IU", "ANMO", "BH?")
    client.run()
client.close()
```

This is a runtime pattern, not a network-verification claim. Handle
`EasySeedLinkClientException`, server termination, malformed capabilities, and
reconnect policy. Keep streaming separate from finite FDSN/SDS retrieval.
