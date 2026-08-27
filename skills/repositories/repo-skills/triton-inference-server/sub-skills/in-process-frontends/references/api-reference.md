# API Reference

## Package roles

- `tritonserver` creates and controls an embedded Triton server.
- `tritonfrontend` provides Python bindings for frontend services on top of an embedded server.

## Observed frontends

- `KServeHttp(server, options=None)`
- `KServeGrpc(server, options=None)`
- `Metrics(server, options=None)`

## Option defaults

- `KServeHttp.Options(address='0.0.0.0', port=8000, reuse_port=False, thread_count=8, header_forward_pattern='')`
- `KServeGrpc.Options(address='0.0.0.0', port=8001, reuse_port=False, use_ssl=False, server_cert='', server_key='', root_cert='', use_mutual_auth=False, keepalive_time_ms=7200000, keepalive_timeout_ms=20000, keepalive_permit_without_calls=False, http2_max_pings_without_data=2, http2_min_recv_ping_interval_without_data_ms=300000, http2_max_ping_strikes=2, max_connection_age_ms=0, max_connection_age_grace_ms=0, infer_compression_level=0, infer_thread_count=2, infer_allocation_pool_size=8, max_response_pool_size=2147483647, forward_header_pattern='')`
- `Metrics.Options(address='0.0.0.0', port=8002, thread_count=1)`

## Behaviors to remember

- The option dataclasses validate type and range.
- `KServeHttp` and `KServeGrpc` can be used as context managers.
- `Metrics` exposes the Prometheus endpoint when started.
- The binding layer mirrors native server options; do not treat the Python wrapper as a separate server implementation.
