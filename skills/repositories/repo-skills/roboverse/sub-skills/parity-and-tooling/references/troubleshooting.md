# Parity and Tooling Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Task is not registered | Package discovery/import order or optional task family is absent | Run the bundled registration helper; import the package/selected task family; verify the installed entry point and exact task id. |
| One backend cannot construct the task | Missing simulator extra, asset, driver, display, or unsupported query | Record the backend blocker and run the same config on a supported alternative only if the contract is equivalent. Do not claim a cross-sim result. |
| Large parity delta at step 0 | Different reset state, asset, seed, units, quaternion convention, or camera/action order | Dump aligned initial state and config; compare fields before stepping. |
| Delta grows over time | Timestep/control rate, contact solver, action scale, dynamics, or termination differs | Compare one fixed action per step and each reward/termination term; report closed-loop divergence separately. |
| Both rollouts look successful but parity is false | Visual result hides wrong state/reward or both systems share a bug | Compare tensor/state/reward metrics and task success inputs; never use image similarity as the only gate. |
| Renderer hangs/crashes | Headless/display/EGL/driver issue or unsupported camera | Run import/reset/step without rendering, then one frame with a known supported renderer and timeout. |
| Diagnostic script emits raw import traceback | Optional backend or tool is missing | Use the bundled helper's dependency report; install the exact extra only when the workflow is selected. |
| Conversion changes behavior | Unit/frame/order/schema was inferred rather than declared | Add explicit mapping metadata and round-trip tiny fixtures; stop if source convention is unknown. |
