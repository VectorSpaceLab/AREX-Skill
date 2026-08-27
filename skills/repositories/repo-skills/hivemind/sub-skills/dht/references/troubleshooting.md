# DHT Troubleshooting

## Purpose

Read this when DHT startup, peer discovery, multiaddress handling, or custom coroutine logic fails.

## 1) `Failed to connect to bootstrap peers`

**Symptoms**

- `DHT(..., start=True)` raises a `P2PDaemonError`.
- `hivemind-dht` starts and then exits or never reports a healthy routing table.

**Likely causes**

- `initial_peers` points at the wrong peer ID or port.
- The first peer is not reachable from the second peer's network.
- A firewall, NAT rule, or relay setting blocks the connection.

**Recovery**

1. Re-check the visible multiaddrs from the first peer.
2. Ensure the bootstrap peer is listening on a reachable `host_maddrs` address.
3. For restricted networks, try `client_mode=True`, `use_relay=True`, or `use_auto_relay=True`.
4. If you are testing across machines, prefer public addresses or `use_ipfs=True`.

## 2) `TimeoutError` while waiting for readiness

**Symptoms**

- `wait_until_ready(timeout=...)` times out.
- A peer seems alive but never begins serving traffic.

**Likely causes**

- Bootstrap addresses are valid but no healthy peer answers in time.
- The node is still resolving network settings or relay paths.

**Recovery**

- Increase the timeout only after verifying the addresses.
- Re-run with a more explicit `host_maddrs` / `announce_maddrs` pair.
- Use `hivemind-dht --refresh_period 1` for quicker feedback while debugging.

## 3) `run_coroutine` deadlock or nested-DHT confusion

**Symptoms**

- A custom coroutine never returns.
- The code hangs after calling `run_coroutine` from within the DHT process.

**Likely cause**

- The external `DHT` interface was called from inside the DHT process itself.

**Recovery**

- Only use the external `DHT` object from the host process.
- Keep the custom coroutine fully async and avoid blocking work.

## 4) Identity conflicts

**Symptoms**

- Errors mentioning an identity being already taken by another peer.
- A restarted peer unexpectedly comes up with a new peer ID.

**Likely causes**

- The same `identity_path` is reused by two live peers.
- The file path is missing, not writable, or being shared by accident.

**Recovery**

- Use one identity file per peer.
- Reuse the same `identity_path` only when intentionally restarting the same peer.
- If the peer should change identity each run, omit `identity_path`.

## 5) Multiaddr or relay confusion

**Symptoms**

- `initial_peers` looks right but peers still cannot discover each other.
- A peer can connect locally but not across the internet.

**Likely causes**

- The address uses a localhost or LAN IP when a public address is needed.
- `announce_maddrs` does not match the address other machines can reach.
- Relay or NAT traversal is disabled on a network that needs it.

**Recovery**

- Re-run the first peer and copy the exact visible multiaddrs.
- Add explicit public `announce_maddrs`.
- Enable `use_relay` or `use_auto_relay` when behind NAT.
- For highly constrained networks, try `client_mode=True`.

## 6) When to stop and escalate

Stop local debugging when the issue depends on:

- a firewall or corporate network policy you cannot change
- a missing public address for another machine
- a public relay or IPFS path that is unavailable
- a true code regression in the package itself

In those cases, hand the problem to a broader networking or repo-debugging task and include the exact addresses and error fragment.
