# Driver and model overview

This reference is a policy-selection aid. It describes what the driver
adapter expects; it does not provision models, renderer containers, or assets.
Use the simulation-wizard skill for deployment and cache acquisition.

## Built-in and optional policies

| Config/model name | Camera and history contract | Output/backend facts | Asset and use notes |
|---|---|---|---|
| `manual` / `model_type: manual` | One display camera; context 1 in the standard preset | CPU-only model; output frequency follows driver config; keyboard GUI requires X11 or Wayland | No checkpoint is needed; the schema still requires a placeholder path such as `unused` |
| `vavam` / `model_type: vam` | Exactly one camera; VAM adapter consumes the configured context (the built-in VAM config uses one) | VAM adapter emits at 2 Hz, uses a 900x1600 preprocessing target, and normally uses float16 (float32 on aarch64) | Requires a VAM checkpoint and a JIT tokenizer; model assets are external |
| `vavam_video_model` | One front-wide camera in the documented video-model preset | Same VAM policy, plus driver-side f-theta-to-pinhole rectification; use the 8-frame renderer chunk preset | The video model emits recorded-camera imagery; seed frame, calibration, and map conditioning must agree |
| `alpamayo1` | Configured Alpamayo rig subset, normally four cameras and four frames per camera | bfloat16 VLA; fixed 10 Hz action spacing; requires a sufficiently long ego-pose history | Checkpoint may be a Hugging Face model ID or local release directory; gated/authenticated assets may be required |
| `alpamayo1_5` | Normally four cameras and four frames per camera; language route conditioning | bfloat16, fixed 10 Hz; `use_waypoint_commands: false` in the standard preset | Same external checkpoint/auth boundary as Alpamayo 1; model-specific processor assets are required |
| `alpamayo1_5_1cam` | One `camera_front_wide_120fov` camera; four temporal frames selected with `subsample_factor: 3` | Intended single-view video-model policy; fixed 10 Hz | Keep the matching single-camera renderer preset; do not silently mix four-camera timing |
| `alpamayo1_5_recipes_sft` | Same base temporal/camera contract as Alpamayo 1.5 | Optional recipes/SFT package and checkpoint; not part of the minimal core install | Install the optional recipes dependency only when this policy is needed |
| `alpamayo2` | Normally four cameras and four frames per camera; cameras must be known Alpamayo rig IDs | 32B-class bfloat16 expert; fixed 10 Hz; candidate microbatching can cap peak memory | Use a release-native local directory or supported model ID with config, processor/tokenizer files, and safetensors |
| `transfuser` | Exactly four cameras, exactly one frame per camera, in configured concatenation order | Optional plugin; 2 Hz output; each image is resized/cropped to 270x480 then concatenated horizontally | Checkpoint `.pth` and sibling `config.json` are required; inference is model/torch dependent and normally CUDA-oriented |

The registry is the source of truth for what is installed. A typical core
installation exposes `alpamayo1`, `alpamayo1_5`,
`alpamayo1_5_recipes_sft`, `alpamayo2`, `manual`, and `vam`; `transfuser`
appears only after its plugin distribution is installed. Do not infer
availability from a YAML file or from the presence of a workspace directory.

## Camera and video-model matching

The video-model renderer is stateful: it seeds a rollout with recorded JPEGs,
FTheta calibration, and map conditioning, then returns frames in chunks. The
policy must consume the same view geometry. Use one of these documented
combinations:

```text
single-view VAM:       driver=vavam_video_model +chunking=8frame
a single-view A1.5:     driver=alpamayo1_5_1cam +chunking=8frame
```

`vavam_video_model` rectifies the recorded FTheta frame to the pinhole view
expected by VAM. The normal `vavam` policy assumes its renderer already emits
the pinhole view and does not run the rectifier. The A1.5 single-camera preset
uses `subsample_factor: 3`: video frames are 30 Hz while the policy's image
history is 10 Hz. VaVAM uses one latest image and does not need history
subsampling. The documented OmniDreams recipe is single-view; do not expand
camera count without a renderer/model recipe that supports it.

Chunk duration, simulation control cadence, and driver decision cadence are a
runtime/deployment concern. If a run reports mismatched chunk or frame times,
route the scheduling diagnosis to runtime-services after confirming the policy
preset and camera count here.

## Device, memory, and authentication boundaries

The driver creates a Torch device from configuration but chooses CPU when
CUDA is unavailable. That fallback makes registry and some preprocessing checks
possible; it does not make VAM, Alpamayo, or Transfuser inference practical or
validated on CPU. `manual` is the intentional CPU path.

The 1.5 classifier-free guidance option performs an additional model pass and
can require roughly 60 GB of VRAM according to the configuration contract. The
managed video-model documentation lists approximately 48 GB VRAM for the
VaVAM renderer and 96 GB for the Alpamayo 1.5 renderer. Those figures concern
the complete model/renderer deployment, not a guarantee for every driver-only
process. Alpamayo 2 is a 32B-class model and exposes candidate microbatching to
reduce peak memory; it still requires its model runtime.

Model IDs, gated Hugging Face access, cache mounts, and `HF_TOKEN` belong to the
operator's environment. Authenticate before launch and pass credentials only
through the deployment's documented secret mechanism. Never embed tokens,
weights, cache contents, or private upstream checkouts in a skill or config
committed to a project.
