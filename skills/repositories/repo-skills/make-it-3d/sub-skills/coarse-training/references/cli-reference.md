# `main.py` CLI Reference

This reference summarizes flags discovered from the source parser. The source imports heavy modules before parsing, so `python main.py --help` may fail unless dependencies are installed.

## Run-Mode Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--test` | false | Skip training and render/test from a checkpoint. |
| `--final` | false | After training, run a larger test render; refine block is nested under this branch. |
| `--refine` | false | Intended refine-stage trigger, but source refine execution is under `if opt.final:`. |
| `--save_mesh` | false | Export an OBJ mesh with texture after test/final paths; requires mesh dependencies. |
| `--workspace NAME` | `workspace` | Stored as `results/NAME` inside the source. |
| `--ckpt VALUE` | `latest` | Checkpoint selector/path. |

## Prompt and Guidance Flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--text` | `None` | If omitted, BLIP2 captioning is invoked. |
| `--negative` | empty string | Negative prompt text. |
| `--guidance` | `stable-diffusion` | Choices indicated in help: `stable-diffusion`, `clip`. |
| `--guidance_scale` | `10` | Classifier-free guidance scale. |
| `--need_back` | false | Adds back-view text path. |
| `--suppress_face` | false | Parsed but not prominent in source behavior. |
| `--sd_version` | `2.0` | Choices `1.5`, `2.0`. |
| `--hf_key` | `None` | Custom Hugging Face model id. |

## Training/Renderer Flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--iters` | `10000` | README uses `2000` for phase 1 and `5000` for phase 2. |
| `--refine_iters` | `3000` | Refinement iterations. |
| `--lr` / `--min_lr` | `1e-3` / `1e-4` | Learning-rate controls. |
| `--optim` | `adan` | Choices `adan`, `adam`, `adamw`. Source special-cases `adan`; other values use Adam in the inspected code. |
| `--fp16` | false | Enables amp scaler/autocast paths. |
| `--backbone` | `tcnn` | Choices include `grid`, `tcnn`, `sdf`, `vanilla`, `normal`, but source implements `tcnn` and `vanilla` paths only. |
| `--cuda_ray` | false in parser | Overridden to `True` after parsing. |
| `--max_steps` | `512` | CUDA raymarching maximum sampled steps. |
| `--num_steps` | `64` | Non-CUDA ray steps, but source forces CUDA ray. |
| `--upsample_steps` | `32` | Non-CUDA upsampling steps. |
| `--albedo_iters` | `1000` | README uses `3500` in full-360 phase. |
| `--diff_iters` | `400` | Diffusion/guidance scheduling parameter. |
| `--step_range` | `[0.2, 0.6]` | Diffusion timestep range fraction. |

## Camera/Input Flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--ref_path` | `None` | Alpha reference image path; required for practical training. |
| `--w`, `--h` | `128`, `128` | Training render resolution. |
| `--W`, `--H` | `800`, `800` | GUI/test render resolution. |
| `--radius_range` | `[1.0, 1.5]` | Camera radius sampling. |
| `--fov` | `20` | Base training FOV. README suggests `60` for long geometry. |
| `--fovy_range` | `[15, 25]` | Random FOV range for non-front views. |
| `--theta_range` | `[70, 110]` | Elevation range in degrees. |
| `--phi_range` | `[0, 360]` | Azimuth range. README phase 1 uses `135 225`. |
| `--blob_density` | `5` | Gaussian density prior strength. |
| `--blob_radius` | `0.1` | README suggests `0.2` for long geometry. |
