# ONNX Reference and Backend-Test Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Reference output differs from a backend runtime | The backend may be wrong, but ONNX reference semantics also may expose a spec bug | Re-run with a tiny model and inspect `ReferenceEvaluator` intermediate values; treat the ONNX spec/reference behavior as the baseline. |
| Import fails for `onnx.reference` image ops | Optional Pillow/reference extra not installed | Install `onnx[reference]` only if the workflow needs image-decoder/reference coverage. |
| `ReferenceEvaluator` cannot execute an operator | The op may be unimplemented in the reference package or require optional extras | Simplify to a tiny model, check the selected op's reference implementation, and document the missing coverage if the spec path is still acceptable. |
| `backend-test-tools generate-data` produces huge output or tries to download models | The default backend corpus includes real model cases | Use the bounded helper script in this sub-skill, keep to local tiny cases, and avoid real-model downloads unless explicitly required. |
| Backend test expectations are unclear | Node tests and model tests use different fixtures and expectations | Read the local corpus through the helper script and keep the generated output rooted in a temp directory. |
| A custom backend interface implementation misbehaves | The backend base API was misunderstood | Check `onnx.backend.base.Backend`, `BackendRep`, and `Device` signatures first before debugging specific model execution. |
