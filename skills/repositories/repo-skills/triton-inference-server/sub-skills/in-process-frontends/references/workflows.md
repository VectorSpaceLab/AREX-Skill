# Python In-Process Workflows

## Typical sequence

```python
import tritonserver
from tritonfrontend import KServeHttp, KServeGrpc, Metrics

server = tritonserver.Server(tritonserver.Options(model_repository='/models')).start(wait_until_ready=True)
http = KServeHttp(server)
grpc = KServeGrpc(server)
metrics = Metrics(server)
http.start(); grpc.start(); metrics.start()
# ... client calls ...
metrics.stop(); grpc.stop(); http.stop(); server.stop()
```

## Context manager pattern

Use the context manager when the workflow is short and cleanup should be automatic:

```python
with KServeHttp(server) as http:
    ...
```

## Supported surfaces and limits

- The Python bindings expose KServe HTTP, KServe gRPC, and metrics frontends.
- Tracing, shared memory, restricted protocols, Vertex AI, and SageMaker are not fully supported when launching frontends through the Python bindings in the current docs.
- If a client sends inference after the server is already stopped, shutdown order was wrong or the application kept a stale client object alive.
