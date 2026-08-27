# Client Library Recipes

## Python HTTP client pattern

```python
import tritonclient.http as httpclient
client = httpclient.InferenceServerClient(url='localhost:8000')
```

## Python gRPC client pattern

```python
import tritonclient.grpc as grpcclient
client = grpcclient.InferenceServerClient(url='localhost:8001')
```

## Tensor workflow

1. Create inputs with the exact model tensor name, shape, and datatype.
2. Use `set_data_from_numpy` or the equivalent client setter for the chosen transport.
3. Add outputs by name.
4. Call `infer` or stream inference as appropriate.
5. Parse outputs by output tensor name.

## Streaming, timeouts, and shared memory

- Use gRPC streaming only when the same connection/order guarantees are needed.
- Use shared memory only when the user has approved same-host data-movement optimization.
- Use timeouts and cancellations when a request may stall or a model may be overloaded.

## curl recipes

Use `curl` for health, metadata, and simple inference diagnostics only when the payload is easy to construct and the user wants a transport-agnostic check.
