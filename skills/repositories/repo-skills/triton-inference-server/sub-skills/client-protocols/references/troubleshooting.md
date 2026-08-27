# Protocol Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| HTTP 404/400 on infer | Wrong model name, version, endpoint, or malformed payload | Check `/v2/models/<model>/config` or repository config before retrying. |
| gRPC `INVALID_ARGUMENT` | Tensor shape, datatype, or binary/body mismatch | Compare request metadata to model config and rebuild the request descriptor. |
| BYTES request fails | Incorrect BYTES encoding or tensor type | Use the helper and confirm the client library's BYTES conventions. |
| Shared memory request fails | Region not registered or backend/client mismatch | Verify shared-memory setup and host/GPU prerequisites. |
| Health ready but infer fails | Model/backend failure rather than server startup issue | Split the layer: server ready vs model ready vs inference format. |
| OpenAI frontend prompt expected | Request was sent to KServe `/v2/*` | Route to the OpenAI frontend sub-skill instead. |
