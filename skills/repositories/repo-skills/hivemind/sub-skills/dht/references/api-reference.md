# DHT API Reference

## Purpose

Read this when you need the verified DHT constructor options, the store/get contract, or the low-level network knobs that affect peer discovery.

## Verified top-level API

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `hivemind.DHT` | `DHT(initial_peers=None, *, start, p2p=None, daemon=True, num_workers=4, record_validators=(), shutdown_timeout=3, await_ready=True, **kwargs)` | High-level wrapper around a background `DHTNode`. |
| `DHT.get` | `get(self, key, latest=False, return_future=False, **kwargs)` | Returns `ValueWithExpiration` or `None`; `return_future=True` gives an `MPFuture`. |
| `DHT.store` | `store(self, key, value, expiration_time, subkey=None, return_future=False, **kwargs)` | Stores a msgpack-serializable value until expiration. |
| `DHT.run_coroutine` | `run_coroutine(self, coro, return_future=False)` | Runs custom async logic inside the DHT process. |
| `DHT.get_visible_maddrs` | `get_visible_maddrs(self, latest=False)` | Returns the visible multiaddrs other peers should use. |
| `DHT.shutdown` | `shutdown(self)` | Terminates the background DHT process. |
| `DHT.wait_until_ready` | `wait_until_ready(self, timeout=None)` | Raises a timeout if the node never becomes ready. |
| `hivemind.dht.DHTNode.create` | `create(p2p=None, node_id=None, initial_peers=None, bucket_size=20, num_replicas=5, depth_modulo=5, parallel_rpc=None, wait_timeout=3, refresh_timeout=None, bootstrap_timeout=None, cache_locally=True, cache_nearest=1, cache_size=None, cache_refresh_before_expiry=5, cache_on_store=True, reuse_get_requests=True, num_workers=4, chunk_size=16, blacklist_time=5.0, backoff_rate=2.0, client_mode=False, record_validator=None, authorizer=None, ensure_bootstrap_success=True, strict=True, **kwargs)` | Lower-level node constructor used by `DHT`. |
| `DHTNode.get` | `get(self, key, latest=False, **kwargs)` | Low-level async fetch. |
| `DHTNode.store` | `store(self, key, value, expiration_time, subkey=None, **kwargs)` | Low-level store primitive. |

## Networking knobs worth remembering

These are passed through `DHT(..., **kwargs)` into the lower layers:

- `host_maddrs`: listen addresses for incoming connections.
- `announce_maddrs`: externally visible addresses other peers should use.
- `client_mode`: join and query a DHT without advertising yourself as a server.
- `use_relay`: enable or disable libp2p relay support.
- `use_auto_relay`: try to find relay paths automatically.
- `use_ipfs`: use IPFS to help peers discover one another.
- `identity_path`: make the peer ID deterministic across restarts.
- `no_listen`: start in a client-only network mode.
- `force_reachability`: used by the lower-level P2P layer to simulate a public or private host.

## Record behavior

- Keys and values must be msgpack-serializable.
- `expiration_time` is an absolute DHT timestamp, usually created with `hivemind.utils.timed_storage.get_dht_time() + seconds`.
- `subkey=` lets multiple peers contribute subrecords under one key instead of overwriting each other.
- `latest=True` asks for the freshest visible value instead of the first valid one.
- `run_coroutine(..., return_future=True)` is the safe way to trigger background DHT work and later wait on it.

## Lower-level network API

The public `hivemind.p2p.P2P` layer is mainly an implementation detail for DHT and MoE, but these verified options explain the DHT CLI and debugging knobs:

| Symbol | Verified signature / behavior | Notes |
| --- | --- | --- |
| `P2P.create` | `create(initial_peers=None, *, announce_maddrs=None, auto_nat=True, conn_manager=True, dht_mode='server', force_reachability=None, host_maddrs=('/ip4/127.0.0.1/tcp/0',), identity_path=None, idle_timeout=30, nat_port_map=True, relay_hop_limit=0, startup_timeout=15, tls=True, use_auto_relay=False, use_ipfs=False, use_relay=True, persistent_conn_max_msg_size=4194304, quic=None, use_relay_hop=None, use_relay_discovery=None, check_if_identity_free=True, no_listen=False, trusted_relays=None)` | Advanced peer setup. |
| `P2P.replicate` | `replicate(daemon_listen_maddr)` | Reuses an existing daemon's listen address. |
| `ServicerBase.add_p2p_handlers` | `add_p2p_handlers(self, p2p, wrapper=None, *, namespace=None, balanced=False)` | Mostly relevant when writing custom RPC handlers. |
| `ServicerBase.get_stub` | `get_stub(p2p, peer, *, namespace=None)` | Creates a client stub for a remote peer. |

## Validation sources

- Verified from installed package signatures and CLI help.
- Cross-checked against `docs/modules/dht.rst`, `docs/user/dht.md`, and `tests/test_dht.py` / `tests/test_cli_scripts.py`.
