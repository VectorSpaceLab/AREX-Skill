# gRPC and SDK Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Connection refused on `:3774` | Core gRPC server not running or wrong address. | Start `bindu serve --grpc` or fix `coreAddress`; free port. |
| Registration `success=false` | Bad JSON/config/skills or HTTP port conflict. | Inspect core logs, validate config, check `deployment.url` port. |
| TS registration fails when core already running | Stale/incompatible core or occupied HTTP port. | Stop stale core or align versions and ports. |
| A2A task fails after registration | Core cannot call SDK callback or handler errored. | Check callback server, network namespace, handler logs. |
| Handler timeout | SDK handler exceeds core timeout. | Shorten work, increase timeout intentionally, or return `input-required`. |
| Heartbeat unknown agent | Core restarted or registration failed but loop continued. | Re-register and stop stale SDK process. |
| Proto/service errors | Core and SDK proto/generated outputs drifted. | Regenerate all stubs from the proto. |
| State response completes unexpectedly | SDK did not set non-empty supported `state`. | Return `state: "input-required"` or `"auth-required"` plus prompt. |
| Streaming expected but absent | TypeScript unary path is standard. | Use unary responses unless streaming has been implemented end-to-end. |
| Skills missing | Wrong working directory or missing skill files. | Use correct skill paths or inline skill definitions. |
| gRPC message too large | Oversized raw skill docs or history. | Split/reduce docs or intentionally tune message size. |
