# Hunyuan3D-2 Cross-cutting Troubleshooting

Use this root troubleshooting page to route failures to the right sub-skill.

## Quick routing table

| Symptom/task | Go to |
| --- | --- |
| `from_pretrained` downloads, wrong subfolder, CUDA OOM during shape, multiview dict issue, FlashVDM issue | `sub-skills/shape-generation/references/troubleshooting.md` |
| `custom_rasterizer`, `mesh_processor`, `MeshRender`, UV wrapping, texture OOM, pymeshlab/OpenGL, textured export issue | `sub-skills/texture-and-mesh/references/troubleshooting.md` |
| API server/Gradio start, port mismatch, HTTP 404 JSON, `/send` polling, Blender add-on payloads | `sub-skills/services-and-integrations/references/troubleshooting.md` |
| PyTorch CUDA install, CUDA headers, extension build, package conflicts, model cache setup | `sub-skills/environment-and-model-setup/references/troubleshooting.md` |

## Non-negotiable backend fact

For this skill's scope, real shape generation, texture generation, FlashVDM, and VAE encode/decode require CUDA. CPU-only parser checks, imports, and dry-runs are useful but are not generation proof.

## Common first checks

```bash
python sub-skills/environment-and-model-setup/scripts/check_install.py --json
python sub-skills/environment-and-model-setup/scripts/check_install.py --check-cuda --check-extensions --json
```

If these fail, fix the environment before debugging model quality or service payloads.

## Avoid stale docs

Some installation/workflow pages in the distilled source checkout contained unrelated placeholder text. Prefer README/model-zoo-derived guidance and the bundled references in this skill.

## Model cache/network safety

Full runs can download large Hugging Face subfolders. Before running non-dry commands, decide:

1. Which model repo/subfolder is needed.
2. Whether weights are already cached through `HY3DGEN_MODELS` or `~/.cache/hy3dgen`.
3. Whether network and GPU time are approved.
4. Whether outputs should be GLB, OBJ, PLY, STL, or service binary response.

## Import order for texture extension checks

Always import `torch` before direct `custom_rasterizer` import. If not, the process may fail because PyTorch shared libraries are not loaded.
