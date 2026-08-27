# DragGAN UI Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| No model in the dropdown or `No network pickle loaded` | Empty cache/checkpoint directory or wrong suffix | Run the root model preflight; place readable `.pkl` files in the directory passed to the helper. |
| `Cannot infer model type from pkl name!` | Filename lacks `stylegan2`, `stylegan3`, or `stylegan_human` | Rename a copy to preserve the family signal, then rerun preflight. |
| CUDA event/device error | CPU-only PyTorch or missing GPU visibility | Run the root environment helper; use a CUDA PyTorch build for interactive editing. Do not treat CPU generation as a UI pass. |
| Window does not open | Missing display, GLFW/OpenGL library, or headless session | Use Gradio, configure a display/virtual display, and verify `glfw`, `imgui`, and PyOpenGL imports. |
| Gradio fails during import | New `gradio_client` or removed `pkg_resources` compatibility | Use the repo-compatible Gradio 3 dependency family and run the helper in dry-run mode first. |
| Drag does nothing | Incomplete point pairs, no target, or mask excludes the intended region | Reset points, create source then target pairs, show/reset the mask, and start again. |
| Drag changes too much | `w` space, high step size, broad mask, or large motion lambda | Prefer `w+`, lower learning rate/step size, constrain the flexible mask, and change one control at a time. |
| Drag is too slow or unstable | High-resolution model, `w+`, large iteration count, or insufficient VRAM | Test a smaller checkpoint/region first, reduce controls, and monitor GPU memory. |
| Gradio server is reachable only locally | App was not started with `--listen` | Add `--listen`; use `--share` only when a public temporary link is acceptable. |
