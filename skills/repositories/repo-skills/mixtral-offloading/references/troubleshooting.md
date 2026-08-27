# Cross-cutting troubleshooting

| Area | Symptom | Route / fix |
| --- | --- | --- |
| Source-only import | `ModuleNotFoundError: src...` | Add the user's checkout root to `PYTHONPATH` or `sys.path`; there is no installable local package metadata. |
| Dependencies | Version or import errors after installing broad packages | Reinstall the repo runtime requirements in an isolated environment; avoid mutating shared environments without approval. |
| CUDA | CPU import works but inference/kernel fails | CPU import is not CUDA verification. Run `scripts/check_environment.py --require-cuda` and the quantization Triton smoke if kernels matter. |
| HQQ warning | `hqq_aten package not installed` | Document as optional ATEN backend absence; the repo path uses HQQ/Triton, not ATEN. |
| Full demo | Downloads or interactive loop block automation | Separate download approval, state validation, and bounded generation. Do not run notebook-style shell cells blindly. |
| State files | Missing safetensors index or `w1.W_q` key | Use the inference sub-skill to validate the quantized offloading state layout. |
| Quantization | Group-size or packing errors | Use the quantization-kernels sub-skill; run packing round-trip and inspect HQQ metadata shape/group sizes. |
| Cache/offload | `Cache is full`, no evictable experts, duplicate UID | Use the expert-cache sub-skill; recompute main/offload sizes and inspect UID/group invariants. |

## Escalation path

1. Verify environment and source imports.
2. Decide whether the failing workflow truly needs CUDA.
3. Use the narrow sub-skill for the failing layer: inference, quantization, or
   expert-cache.
4. Preserve large-download and long-run approvals separately from smoke checks.
5. If the user asks for new quantization methods or speculative prefetching,
   treat them as extension work: the README describes them as future work, not
   implemented behavior.
