# model-backends troubleshooting

Use this page when a model backend is misregistered, resolves to the wrong class, or fails because an optional backend dependency is missing.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The backend resolves as simple when the user expected chat | The registry selected the simple manifest or `force_simple=True` was used | Confirm the model id and inspect the manifest with `model_registry_smoke.py`. |
| `is_simple` validation errors | The class flag does not match the registry entry | Fix the backend registration and the class flag together. |
| `model_args` are ignored or malformed | The request is passing provider-specific settings in the wrong format | Compare the intended backend against `api-reference.md` and the registry manifest. |
| `torchcodec`, `decord`, `vllm`, or `sglang` imports fail | The optional backend package is missing from the install | Install only the needed extra and rerun the registry smoke. |
| Video decoding falls back to the wrong path | `LMMS_VIDEO_DECODE_BACKEND` is unset or points at an unavailable backend | Use `video_decode_smoke.py` to confirm which decode helpers are importable. |
| Throughput or timing metrics are missing | The backend does not emit those metrics or the selected path does not collect them | Verify the backend family and check the throughput documentation before changing code. |
| CUDA or device placement errors appear on local models | The runtime lacks a usable GPU backend or the backend expects a different device map | Check the installed wheel, device visibility, and the backend's documented defaults. |

## Fast recovery steps

1. Resolve the requested model id and alias first.
2. Confirm whether the model should be chat or simple.
3. Check optional dependencies before editing backend code.
4. For media-heavy workflows, confirm the decode backend separately.
5. Use the smoke scripts before opening the source tree for a backend bug.
