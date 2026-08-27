# Envision, recording, replay, and Visdom

Envision has three operational pieces: the SMARTS `Client`, an Envision server
that accepts websocket state broadcasts, and a browser frontend. This skill
covers the first two only. Frontend npm development and raw media are excluded.
Use the sibling `cli-integrations` route for exact `scl` command syntax.

## Client modes

The client defaults to `ws://localhost:8081`. Its useful constructor fields are:

```python
from envision.client import Client

live = Client(endpoint="ws://localhost:8081", headless=False)
recording = Client(output_dir="./records", headless=True)
```

`headless=False` starts a background websocket process that retries while data
is queued. `headless=True` suppresses the live connection. Supplying
`output_dir` starts a separate JSONL writer; the implementation creates a
 timestamped run directory and a client-specific `.jsonl` file. Always call
`teardown()` or destroy the owning environment so queue processes flush and
join. Use a finite output directory under the caller's workspace, not a
checkout-dependent path.

The public environment wrappers expose the same concept as
`envision_record_data_replay_path`. The documented end-to-end workflow expects
an Envision server for recording and replay. The current client implementation
can write local JSONL with `output_dir` independently of the live websocket,
including in headless mode; treat that as a local diagnostic and verify the
file before relying on it. Browser playback and server-side replay still need a
server.

## Server and endpoint checks

The bundled rendering helper only probes the endpoint and never starts a
service. The default HTTP/websocket port is 8081. A live server should expose
an HTTP page and accept a websocket path under the simulation id. If the server
is absent, a non-headless client logs a first connection warning and may retry,
which can make teardown or image-heavy runs appear slow. For CPU tests use
`envision=None` in the environment route, or use the client's headless mode.
Do not launch a long-lived server from a skill helper.

If a server is intentionally used, run it by the project's approved service
procedure and keep the port/host explicit. Remote browser access normally
requires forwarding the server port; that is an infrastructure concern, not a
sensor import check.

## Record layout and replay

A recording root contains one or more timestamped run directories, each with
one JSONL file per client/simulation. `inspect_replay_records.py` reports file
count, line count, byte size, JSON validity, and the broad shape of the first
records without sending them anywhere.

The Python replay primitive is:

```python
Client.read_and_send(
    path="./records/<run>/<client>.jsonl",
    endpoint="ws://localhost:8081",
    fixed_timestep_sec=0.1,
)
```

It reads lines, sleeps between sends, and forwards already serialized state;
it does not validate that a server is available before starting. Keep the
`timestep` positive and bounded. For multiple files, the public CLI route may
send them concurrently; check the endpoint and file count first. Never use a
recording helper as a substitute for a simulation run or source scenario.

## Data filtering and formatting

`EnvisionStateFilter` can override actor/simulation attributes and cap iterable
counts. `EnvisionDataFormatterArgs` controls decimal rounding, boolean encoding
(as integers by default), and reduction. Reduced streams append a mapping and a
removed-id list to the serialized layer. The custom JSON encoder converts NumPy
arrays to lists and non-finite floats to the strings `Infinity`, `-Infinity`,
and `NaN`. Consumers should not assume strict JSON numeric non-finites.

The server stores frames in memory with a bounded capacity and may discard
random middle frames under pressure while preserving early and recent frames.
Large camera/point-cloud streams therefore increase memory and can make replay
history sparse. Reduce image dimensions, actor counts, or Envision state fields
before increasing server capacity.

## Optional Visdom

Visdom is not part of the verified baseline. Install the `visdom` extra only
when the host already permits that optional service, set the SMARTS Visdom
configuration explicitly, and start a separately managed Visdom server on its
chosen port (commonly 8097). A missing Visdom package or server must not block
CPU sensors, Panda3D import checks, or Envision JSONL inspection. This route
neither starts Visdom nor bundles its web assets.
