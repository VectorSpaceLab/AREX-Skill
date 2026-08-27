# Inference Troubleshooting

## Purpose

Read this when model loading or evaluation fails.

## Common issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Supernet load succeeds but a forward pass fails | Torch wheel/backend mismatch or a bad device choice. | Reinstall a matching `torch` / `torchvision` pair and rerun the bundled smoke on CPU first. |
| Specialized model tries to download files | The helper resolves public configs or weights on demand. | Allow network access, cache the files, or switch to a supernet smoke first. |
| `ImageFolder` cannot find the validation split | The folder structure does not match ImageNet-style expectations. | Point the script at a directory with the expected validation layout. |
| CPU evaluation is very slow | Specialized-model validation is benchmark-oriented and is usually better on CUDA. | Use CPU only for smoke checks, and move benchmark-style runs to a GPU session. |
| `--sample-subnet` produces a different shape than expected | The sampled subnet changed the runtime architecture. | Use `get_active_subnet(preserve_weight=True)` and inspect `module_str` before evaluating. |

## Practical recovery

- For offline smoke checks, load `ofa_net(..., pretrained=False)` and avoid public downloads.
- For specialized ids, use the returned `image_size` instead of hard-coding 224.
- If a run only needs to prove that the API works, the bundled helper's forward
  smoke is enough.
- If a run needs benchmark-quality subnet evaluation, use a real validation split
  and a CUDA-capable backend.
