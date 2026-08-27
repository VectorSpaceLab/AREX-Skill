# Private Swarms

A private Petals swarm uses a DHT bootstrap node plus one or more servers that announce model block ranges to that DHT. Clients then use the same `initial_peers` and model/DHT prefix.

## Pattern

1. Start a DHT bootstrap node on a known address and optional deterministic identity.
2. Read the peer ID from the DHT process and form a multiaddr such as `/ip4/HOST/tcp/PORT/p2p/PEER_ID`.
3. Start servers with the target model, `--initial_peers` set to that multiaddr, explicit device/dtype, and explicit block selection for small tests.
4. Use the same `initial_peers` in client `from_pretrained(...)` calls.
5. Track PIDs and clean up DHT/server processes on success, failure, timeout, or interruption.

The builder prints a plan with a placeholder peer ID:

```bash
python scripts/build_private_swarm_commands.py --model MODEL_ID --server-count 2 --device cpu --torch-dtype float32 --blocks-per-server 2 --throughput 1 --loopback-only
```

Replace the placeholder after the DHT prints its actual peer ID. Loopback-only addresses are for same-host tests; public operation needs intentional ports and announce addresses.
