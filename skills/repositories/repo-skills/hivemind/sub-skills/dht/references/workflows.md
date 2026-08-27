# DHT Workflows

## Purpose

Read this for the practical steps to start a DHT, join an existing swarm, store and fetch records, and tune internet-facing peers.

## 1) Start a first node

```python
from hivemind import DHT

dht = DHT(start=True)
print("Visible peers:", [str(addr) for addr in dht.get_visible_maddrs()])
```

What this means:

- The first peer usually listens on localhost-only addresses by default.
- `get_visible_maddrs()` returns the addresses another peer should use in `initial_peers`.
- If you want peers outside your machine or LAN, set explicit `host_maddrs` and `announce_maddrs`.

## 2) Join a running DHT

```python
from hivemind import DHT

peer = DHT(initial_peers=dht.get_visible_maddrs(), start=True)
```

Use the first peer's visible multiaddrs, or the public/relay/IPFS address list for an internet-connected node.

## 3) Store and fetch records

```python
from hivemind import DHT
from hivemind.utils.timed_storage import get_dht_time

dht = DHT(start=True)
ok = dht.store("my_key", ("i", "love", "bees"), expiration_time=get_dht_time() + 600)
value = dht.get("my_key", latest=True)
```

Notes:

- `expiration_time` is absolute DHT time, not a relative delay.
- `subkey=` is how several peers contribute to one key without overwriting one another.
- `return_future=True` gives you an `MPFuture` when you want to overlap the lookup with other work.

## 4) Run custom DHT logic

Use `run_coroutine(...)` for custom async work that must run in the DHT process.

```python
async def publish_heartbeat(dht, node):
    await node.get("heartbeat", latest=True)
    return True

result = dht.run_coroutine(publish_heartbeat)
```

Good uses:

- bespoke record declarations
- custom health checks
- peer discovery helpers

Avoid:

- calling the external `DHT` interface from inside the DHT process itself
- blocking the coroutine with long synchronous work

## 5) Make the peer reachable on the internet

Common patterns:

- `host_maddrs=["/ip4/0.0.0.0/tcp/0", "/ip4/0.0.0.0/udp/0/quic"]`
- `announce_maddrs=[...]` with publicly reachable addresses
- `client_mode=True` when the peer sits behind a restrictive firewall
- `use_relay=True` / `use_auto_relay=True` when relays are needed
- `use_ipfs=True` when you want IPFS-assisted peer discovery

## 6) Use the installed CLI

The package exposes `hivemind-dht` as the runtime command for this workflow.

Typical uses:

```bash
hivemind-dht --host_maddrs /ip4/127.0.0.1/tcp/0 --refresh_period 1
hivemind-dht /ip4/127.0.0.1/tcp/12345/p2p/PEER_ID --host_maddrs /ip4/127.0.0.1/tcp/0
```

## 7) Readiness check

Before asking another agent to reason about DHT behavior, run the bundled preflight:

```bash
python scripts/check_install.py
```

Add `--check-cuda` only if you want to confirm the host's CUDA stack as well.
