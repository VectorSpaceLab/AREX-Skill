# Data-access API reference

This reference summarizes public ObsPy interfaces relevant to acquisition. It
is a compact operating reference, not a replacement for a provider's FDSN
service documentation.

## FDSN clients

```python
from obspy import UTCDateTime
from obspy.clients.fdsn import Client, RoutingClient

t0 = UTCDateTime("2020-01-01T00:00:00Z")
t1 = UTCDateTime("2020-01-01T00:10:00Z")
client = Client("EARTHSCOPE", timeout=120)
stream = client.get_waveforms("IU", "ANMO", "00", "LHZ", t0, t1)
inventory = client.get_stations(network="IU", station="ANMO",
                                 starttime=t0, endtime=t1,
                                 level="channel")
catalog = Client("ISC").get_events(starttime=t0, endtime=t1,
                                     minmagnitude=4)
```

| Public interface | Important inputs | Result / notes |
| --- | --- | --- |
| `Client(base_url="EARTHSCOPE", major_versions=None, user=None, password=None, user_agent=..., debug=False, timeout=120, service_mappings=None, force_redirect=False, eida_token=None, _discover_services=True, use_gzip=True)` | Shortcut or HTTP(S) base URL; explicit timeout; optional auth only when supplied by the user | Discovers available `dataselect`, `station`, and/or `event` services at construction by default. Use `_discover_services=False` only when discovery is intentionally avoided. |
| `Client.get_waveforms(network, station, location, channel, starttime, endtime, quality=None, minimumlength=None, longestonly=None, filename=None, attach_response=False, **kwargs)` | NSLC selectors, UTC bounds; `*`/`?` and comma lists are supported | Returns `Stream`, or writes raw response when `filename` is supplied. `attach_response` is deprecated and not a substitute for explicit response handling. |
| `Client.get_stations(..., network=None, station=None, location=None, channel=None, level=None, includerestricted=None, includeavailability=None, matchtimeseries=None, filename=None, format=None, **kwargs)` | Temporal, NSLC, geographic, and `level` filters | Returns `Inventory`; `level` may be `network`, `station`, `channel`, or `response`. `format="xml"` requests StationXML; `format="text"` requests FDSN station text. |
| `Client.get_events(..., starttime=None, endtime=None, minlatitude=None, maxlatitude=None, minlongitude=None, maxlongitude=None, latitude=None, longitude=None, minradius=None, maxradius=None, mindepth=None, maxdepth=None, minmagnitude=None, maxmagnitude=None, eventid=None, limit=None, offset=None, orderby=None, filename=None, **kwargs)` | Time, bounding box/radius, depth/magnitude, event ID, ordering | Returns `Catalog`, or raw output with `filename`. Provider capability varies; unsupported optional parameters can warn or fail. |
| `Client.get_waveforms_bulk(bulk, ...)` | Non-empty iterable of `(network, station, location, channel, start, end)` rows | Batches multiple waveform selectors into one request. Keep the list finite and inspect each returned trace. |
| `RoutingClient("earthscope-federator" or "eida-routing", ...)` | Route type, timeout, optional provider include/exclude | Returns combined waveform/station results across providers. Routing clients support `get_waveforms*` and `get_stations*`, not events; `filename` and `attach_response` are unsupported. |

FDSN location encoding uses `--` for a blank location in query strings. The
low-level public helpers `convert_to_string()` and `build_url()` provide the
package's timestamp and URL behavior, but prefer the high-level methods for
normal requests. Inspect a planned URL rather than treating URL construction
as a network test.

## Local archives

```python
from obspy import UTCDateTime
from obspy.clients.filesystem.sds import Client as SDSClient
from obspy.clients.filesystem.tsindex import Client as TSIndexClient

sds = SDSClient("/data/archive", sds_type="D", format="MSEED",
                fileborder_seconds=30, fileborder_samples=5000)
st = sds.get_waveforms("IU", "ANMO", "", "HHZ", t0, t1, merge=-1)
ratio, gap_count = sds.get_availability_percentage(
    "IU", "ANMO", "", "HHZ", t0, t1)

index = TSIndexClient("/data/timeseries.sqlite",
                      datapath_replace=("^", "/data/archive/"))
extents = index.get_availability_extent(network="IU", channel="BHZ")
spans = index.get_availability(network="IU", channel="BHZ",
                               starttime=t0, endtime=t1,
                               merge_overlap=True)
st = index.get_waveforms("IU", "ANMO", "10", "BHZ", t0, t1)
```

### SDS layout

SDS waveform files normally follow:

```text
<SDS-root>/<YEAR>/<NET>/<STA>/<CHAN>.<TYPE>/<NET>.<STA>.<LOC>.<CHAN>.<TYPE>.<YEAR>.<DOY>
```

`SDSClient.get_waveforms()` accepts NSLC wildcards, reads matching daily files
including nearby day boundaries, trims to the requested interval, and by
default performs a conservative merge (`merge=-1`). Set `merge=None`/`False`
to retain separate segments; do not confuse a separate segment with a missing
file until `get_gaps()` or availability is checked.

`get_availability_percentage()` returns `(fraction_available, gap_count)`.
`has_data()` checks for matching archive files, while `get_all_nslc()` and
`get_all_stations()` enumerate local archive contents. These scans can be slow
on network filesystems.

### TSIndex

TSIndex `Client` reads an existing SQLite index and the indexed MiniSEED data;
`datapath_replace` is useful when paths recorded by the index differ from the
current local mount. Wildcards and comma-separated selectors are supported.
`get_availability_extent()` returns `(net, sta, loc, cha, earliest, latest)`;
`get_availability()` returns contiguous spans, optionally with sample rate and
merged overlaps; `get_availability_percentage()` returns `(fraction, gaps)`.

## SeedLink

```python
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient

class Collector(EasySeedLinkClient):
    def on_data(self, trace):
        consume(trace)  # bounded by caller-owned policy

client = Collector("seedlink.example:18000", autoconnect=False)
client.connect()
client.select_stream("IU", "ANMO", "BH?")
# client.run() is an unbounded callback loop; arrange shutdown ownership.
```

`get_info("CAPABILITIES")`, `capabilities`, `has_capability()`, and
`has_info_capability()` inspect a connected server before selecting streams.
`select_stream()` requires multi-station capability in this implementation.
`close()` disconnects. `create_client()` is a convenience function that
connects immediately and validates callback callability; do not use it for a
no-network plan.
