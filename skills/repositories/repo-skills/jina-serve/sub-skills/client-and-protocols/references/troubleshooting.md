# Client Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ConnectionError` on `post()` | The Flow/Deployment/Gateway is not reachable, or the protocol/port/host is wrong. | Check `jina ping`, the service logs, and the exact host/protocol/port triple. |
| Requests arrive but callbacks never run | The failure is outside the response stream, such as a network failure or a transport-level disconnect. | Separate executor-level errors from transport failures; callbacks only see stream-local response events. |
| Retry settings do not help | The failure is not transient, or the input generator cannot be replayed cleanly. | Reduce request size, confirm the stream is replayable, and distinguish executor errors from network errors. |
| Client cannot connect over TLS | TLS is configured on the wrong side or host/protocol strings conflict with keyword args. | Use one source of truth: either a host scheme or explicit keyword args, not both. |
| HTTP/WebSocket protocol behaves differently than gRPC | The caller is relying on gRPC-specific streaming semantics. | Pick the protocol that matches the service behavior and expectations before debugging the caller. |
| Responses arrive out of order | Streaming order was not enforced. | Use `results_in_order=True` when ordering matters. |
