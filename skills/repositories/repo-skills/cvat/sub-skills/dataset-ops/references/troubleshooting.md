# CVAT dataset troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Import/export fails with `bad archive`, `unsupported format`, or similar | Wrong dataset format or archive layout | Re-check the exact format name and use the matching CVAT/ML export variant. |
| Shapes or attributes disappear after import/export | Target format does not preserve that structure | Use CVAT XML or Datumaro when fidelity matters; otherwise document the loss as expected. |
| Video task export misses frames or tracks | Format does not support the needed video track semantics | Use a video-capable format and verify track support before exporting. |
| Mask conversion changes results | `conv_mask_to_poly` or mask format transformation is lossy | Prefer a mask-preserving format, or test a tiny sample first and document the loss. |
| `with-images` or `include_images=True` creates a huge archive | Full images were included intentionally | Re-export without images when the downstream system already has them. |
| Remote upload works locally but not in CVAT | The server cannot reach the URL | Test from the CVAT host/container network, not from the client machine. |
| Share-path upload fails | Path is not visible inside the CVAT server deployment | Mount/adjust the server-side share path and retry. |
| Cloud storage id not found | Wrong organization/workspace or storage configuration | Verify the storage belongs to the same CVAT workspace and that the id is correct. |
| `ModuleNotFoundError: torch` for dataset adapter | Optional PyTorch extra missing | Install `cvat-sdk[pytorch]` or use the base dataset layer only. |
| `UnsupportedDatasetError` from PyTorch adapter | Adapter does not support the current task media/layout | Export a dataset format instead of using the adapter. |
| DICOM conversion outputs unreadable images | Bit depth, photometric interpretation, or normalization mismatch | Convert a tiny sample first and inspect output; adjust preprocessing before batch conversion. |
| Manifests cannot be prepared for a video | Too few keyframes or unsupported video layout | Retry with the force option only if you understand the decoding trade-off. |

## Recovery guidance

- Validate a tiny archive or tiny task before processing a large project.
- Keep the original source dataset untouched until the CVAT export/import result has been verified.
- When a format round-trip is lossy, choose a more faithful format rather than stacking conversion steps.
