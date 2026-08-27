# Driver and plugin troubleshooting

Use the smallest safe probe first. Do not run model constructors, checkpoint
downloads, Docker builds, or external scheduler jobs just to diagnose a name or
config problem.

## Install and import

**`PluginNotFoundError: ... not found in alpasim.models`**

1. Run `python scripts/check_driver_plugins.py --group alpasim.models` in the
   exact environment used to launch the wizard.
2. Check the distribution's installed entry-point metadata, not just the
   workspace directory.
3. Install the optional plugin into that environment, then rerun the probe.

**A name is listed but import warnings omit it.** Use the helper's `--load`
mode or a plain Python import to expose the missing dependency. Keep optional
Transfuser/recipes/model packages out of the core environment unless needed.
Do not “fix” an import failure by making the registry silently fall back to a
local class.

**`driver=<plugin>` is unknown while the model name is present.** The model
entry point and the `alpasim.configs` entry point are independent. Inspect both
groups, reinstall the package if config metadata is missing, and ensure the
config package contains the selected driver group. A manual Hydra search-path
override is not the normal repair.

## Optional dependencies, backend, and memory

**The config requests CUDA but logs CPU.** The service explicitly selects CPU
when CUDA is unavailable. Confirm `torch.cuda.is_available()` in the launch
environment and verify that the deployment actually exposes the GPU. CPU
fallback is acceptable for registry/config checks and is the intended manual
path; it does not prove VAM, Alpamayo, or Transfuser inference works on CPU.

**Model import works but construction fails with a missing upstream package.**
Separate interface import from inference readiness. Install the model's declared
optional dependency in the same environment, or switch to a policy whose
requirements are satisfied. Do not bundle the upstream checkout or weights.

**CUDA out-of-memory or a slow first launch.** Start with `max_batch_size: 1`
and one supported policy preset; reduce candidate count or use Alpamayo 2
candidate microbatching where appropriate. Do not lower camera count unless the
model preset supports it. Video-model renderer VRAM and driver VRAM are separate
parts of the complete deployment; route renderer sizing to simulation-wizard.
Classifier-free guidance can require a second pass and materially more memory.

**Hugging Face 401/403 or missing files.** Authenticate in the operator's
runtime, confirm access to the named model/scene asset, and ensure caches are
mounted into the process that loads the model. Do not place `HF_TOKEN` in a
config file or claim a model is ready merely because the model ID parses.

## Data, camera, and config

**Requested camera is missing from the rollout spec.** Compare the exact
logical IDs, including spelling and case, in `inference.use_cameras` with the
vehicle's available cameras. Use the model's documented preset rather than
inventing a camera list.

**Wrong camera count or frame count.** VAM and Transfuser require one camera;
Transfuser also requires exactly one frame per camera. Alpamayo adapters
normally require four cameras and four frames, while the A1.5 single-view
preset uses one camera with `subsample_factor: 3`. The driver returns an empty
trajectory until caches are full; a model validation error after that usually
means the runtime camera interval and config disagree.

**`Image width ... too small`, minimum frame, or unexpected resolution.** The
base adapter resizes by height and center-crops; it does not pad an image that
becomes too narrow. Alpamayo requires at least its declared 320x576 source
minimum. Transfuser normalizes to 270x480 per camera. Render at a supported
resolution or choose the matching preset.

**Rectification errors.** Rectification is only for a camera with FTheta
intrinsics and host-decoded images. Confirm the source resolution, target
intrinsics, and camera logical ID. A one-pixel source mismatch can be cropped;
larger mismatches are rejected. Do not enable `image_decode_device: cuda` with
rectification.

**Video-model frames drift or do not line up with the map.** Preserve the
recorded camera, first-frame JPEG, FTheta calibration, and HD-map conditioning
as one set. Use `vavam_video_model` for VAM's driver-side pinhole conversion or
`alpamayo1_5_1cam` for the matching A1.5 single-view path. Do not inject an
unrelated camera override. Chunk duration and event scheduling belong to
runtime-services.

## CLI and API misuse

**Standalone manual command cannot find `manual`.** Use the installed driver
package's config location with `--config-path=configs --config-name=manual`,
or run the policy through the wizard's `driver=manual` preset. Verify the
command and config are from the same environment.

**A model loads but rejects `output_frequency_hz`.** Alpamayo 1/1.5/2 action
spacing is fixed at 10 Hz; VAM and Transfuser report 2 Hz. Use the model preset
rather than forcing a frequency that the adapter cannot resample.

**Route turns are wrong.** Confirm waypoints are in the true rig frame, check
positive-y-left convention, and inspect `min_lookahead_distance` and
`command_distance_threshold`. Language-conditioned A1.5/A2 policies do not use
the discrete waypoint command, so changing the threshold will not fix their
navigation text.

**A plugin's `predict` receives unexpected images.** The contract is HWC uint8
frames grouped by logical camera, with one frame list per camera and temporal
order preserved. Validate exact keys and lengths before calling upstream code;
do not normalize twice when the upstream processor expects uint8.

## Workflow failures and ownership

**External driver is not reachable.** In `external_static`, the driver process
must already be running and the wizard uses its fixed address. In
`external_dynamic`, the request must carry a reachable address. Check bind
address, container route, port, and `driver_source` before debugging model
inference. The wizard does not launch an external driver.

**Manual window opens but simulation does not advance.** Confirm ego-motion and
camera observations arrive, then check that the GUI thread is alive. The manual
adapter intentionally paces responses to simulation timestamps; it is not a
headless high-throughput policy.

**Native plugin tests skip.** Registry and metadata tests are CPU-safe. Model
inference tests may require Torch, model assets, compiled CUDA dependencies, or
GPU memory; record them as optional rather than substituting a false CPU pass.

When the first failing layer is deployment, service lifecycle, gRPC, or runtime
cadence, hand off to the sibling skill instead of adding a driver workaround.
