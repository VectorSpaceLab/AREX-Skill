# In-Process Frontend Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: libtritonserver.so` | Native library path/version mismatch | Use matching `tritonserver` and `tritonfrontend` packages/runtime libraries. |
| `KServeHttp` not importable from `tritonfrontend` | Optional frontend build variant or incomplete install | Inspect the installed package exports and ensure the frontend binary package is present. |
| Option object rejected | Wrong type or invalid port/thread range | Construct the exact `Options` dataclass and keep values within valid ranges. |
| Client errors after server stop | Shutdown order incorrect | Stop client traffic first, then frontends, then the server. |
| HTTP/gRPC frontend missing tracing/shared-memory/restricted-protocol behavior | Binding limitation | Use the server/container route instead of the Python binding for those features. |
