# Native Sana Image Workflows

This reference covers native Sana `.pth` pipelines, batch prompt files, Sprint,
ControlNet HED, and Gradio image app launch planning. Native generation commands
are CUDA/model-loading commands. Treat them as final-run templates to use only
in an environment that has the Sana native package/entry points, dependencies,
Hugging Face/cache access, and adequate GPU memory.

Use the bundled command planner first:

```bash
python scripts/plan_sana_image_command.py --mode native --native-workflow sana --help
```

The planner prints command shapes and warnings but never imports Sana, loads
weights, starts Gradio, or runs generation.

## Native Python Pipeline: SanaPipeline

Use the native pipeline when a user has a `.pth` checkpoint and matching config.

```python
import torch
from torchvision.utils import save_image
from app.sana_pipeline import SanaPipeline

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
if device.type != "cuda":
    raise RuntimeError("Native Sana image generation requires CUDA for practical use.")

generator = torch.Generator(device=device).manual_seed(42)
sana = SanaPipeline("configs/sana1-5_config/1024ms/Sana_1600M_1024px_allqknorm_bf16_lr2e5.yaml")
sana.from_pretrained("hf://Efficient-Large-Model/SANA1.5_1.6B_1024px/checkpoints/SANA1.5_1.6B_1024px.pth")

image = sana(
    prompt='a cyberpunk cat with a neon sign that says "Sana"',
    height=1024,
    width=1024,
    guidance_scale=4.5,
    pag_guidance_scale=1.0,
    num_inference_steps=20,
    generator=generator,
)
save_image(image, "output/sana.png", nrow=1, normalize=True, value_range=(-1, 1))
```

Native pipeline notes:

- `height` and `width` are requested sizes; the pipeline can use resolution
  binning against Sana's supported aspect-ratio table and crop back to the
  requested size.
- The model latent downsample rate is 32, so unusual dimensions should be
  multiples of 32 or handled through the native aspect-ratio binning path.
- `pag_guidance_scale > 1` uses PAG only when the config has linear attention;
  otherwise native guidance selection falls back to classifier-free.
- A non-empty `negative_prompt` recomputes the null caption embedding and can
  affect future calls on the same pipeline object; reset or reinstantiate when
  comparing prompt variants.

## Native Batch Text-to-Image

The native batch script reads prompts from a text file or JSON file; it does not
accept a direct prompt string as its primary input.

Text prompt file format:

```text
A cyberpunk cat with a neon sign that says 'Sana'.
A small cactus with a happy face in the Sahara desert.
```

Generic command shape:

```bash
python scripts/inference.py \
  --config=configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
  --txt_file=prompts.txt \
  --work_dir=output/sana-batch \
  --sample_nums=10 \
  --bs=1 \
  --cfg_scale=4.5 \
  --pag_scale=1.0 \
  --seed=0
```

JSON prompt format for ordinary image batch inference is a mapping whose keys
become output names and whose values contain a `prompt` field:

```json
{
  "case_0001": {"prompt": "a cyberpunk cat with a neon sign that says Sana"},
  "case_0002": {"prompt": "a small cactus with a happy face in the Sahara desert"}
}
```

Command shape:

```bash
python scripts/inference.py \
  --config=configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
  --json_file=prompts.json \
  --work_dir=output/sana-json \
  --sample_nums=2 \
  --bs=1
```

Output expectations:

- The script creates a `vis/` subdirectory under the chosen work directory.
- The final output directory name encodes dataset, epoch/step when parsed from
  checkpoint name, guidance scale, steps, image size, batch size, sampler, seed,
  dtype, flow shift, guidance type, and image count.
- Files are `.jpg`. JSON mode uses the JSON key as the base filename; text mode
  uses the first 100 characters of the cleaned prompt.
- Existing output files are skipped while advancing the random generator, so a
  rerun can silently skip prompts that already produced images.

Useful options for native batch planning:

| Option | Meaning | Default pattern |
| --- | --- | --- |
| `--config` | Native YAML config; must match checkpoint family | 1024 Sana 1.6B image config |
| `--model_path` | Native `.pth` or `hf://.../checkpoints/*.pth` | Sana 1.6B 1024 `.pth` |
| `--txt_file` | Newline prompt file | sample prompt file label |
| `--json_file` | JSON prompt mapping; overrides text-file mode | `None` |
| `--work_dir` | Parent directory for `vis/` outputs | derived from model path if omitted |
| `--sample_nums` | Max number of prompts to process before slicing | large default |
| `--start_index`, `--end_index` | Prompt slice for sharding | `0`, `30000` |
| `--bs` | Batch size | `1`; keep `1` for custom aspect ratios |
| `--cfg_scale` | Classifier-free guidance scale | `4.5` |
| `--pag_scale` | PAG scale; `1.0` disables PAG effect | `1.0` |
| `--sampling_algo` | `flow_dpm-solver`, `flow_euler`, `dpm-solver`, or `sa-solver` depending on checkpoint/config | `flow_dpm-solver` |
| `--step` | Override default sampling steps | `-1` means algorithm default |
| `--custom_image_size` | Override config image size | `None`; use carefully with aspect-ratio tables |
| `--tar_and_del` | Tar output dir then delete original | disabled; avoid for smoke runs |
| `--if_save_dirname` | Write a metrics temp file with output dirname | disabled; metrics route owns metric use |

## SANA-Sprint Native Workflow

Sprint uses a different model architecture and SCM scheduler. Do not use the
plain Sana batch script for Sprint checkpoints.

```bash
python scripts/inference_sana_sprint.py \
  --config=configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_Sprint_1.6B_1024px/checkpoints/Sana_Sprint_1.6B_1024px.pth \
  --txt_file=prompts.txt \
  --work_dir=output/sana-sprint \
  --sample_nums=10 \
  --bs=1 \
  --cfg_scale=1.0 \
  --sampling_algo=scm \
  --step=2 \
  --seed=0
```

Sprint option notes:

- Default `sample_steps_dict` for `scm` is 2.
- `--max_timesteps` defaults near `1.57080`; `--intermediate_timesteps` defaults
  to `1.3`; a custom `--timesteps` list can override the schedule.
- Source code disables xformers for Sprint by setting `DISABLE_XFORMERS=1`.
  Treat xformers differences as expected for this path.
- The native Sprint app and pipeline expose `height`, `width`,
  `guidance_scale`, `num_inference_steps`, `max_timesteps`,
  `intermediate_timesteps`, and optional custom timestep strings.

Native Sprint API shape:

```python
import torch
from torchvision.utils import save_image
from app.sana_sprint_pipeline import SanaSprintPipeline

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
generator = torch.Generator(device=device).manual_seed(42)
pipe = SanaSprintPipeline("configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml")
pipe.from_pretrained("hf://Efficient-Large-Model/Sana_Sprint_1.6B_1024px/checkpoints/Sana_Sprint_1.6B_1024px.pth")
image = pipe(
    prompt="a tiny astronaut hatching from an egg on the moon",
    height=1024,
    width=1024,
    guidance_scale=4.5,
    num_inference_steps=2,
    generator=generator,
)
save_image(image, "sana_sprint.png", nrow=1, normalize=True, value_range=(-1, 1))
```

## ControlNet HED Native Workflow

Use ControlNet when the user provides a sketch, reference image for HED edge
extraction, or precomputed control map.

ControlNet JSON is a list of objects, not a mapping. Each item must contain:

- `prompt`: non-empty string.
- Exactly one of:
  - `ref_image_path`: input image from which Sana's HED annotator derives a
    scribble/control map.
  - `ref_controlmap_path`: precomputed control map image that bypasses HED
    detection.

Example:

```json
[
  {
    "prompt": "A transparent sculpture of a duck made out of glass.",
    "ref_image_path": "ref_images/duck.jpg"
  },
  {
    "prompt": "A modern living room with stairs, high detail.",
    "ref_controlmap_path": "control_maps/living_room_edges.png"
  }
]
```

Validate before running:

```bash
python scripts/validate_controlnet_request.py --json-file controlnet_request.json
```

Native command shape:

```bash
python tools/controlnet/inference_controlnet.py \
  --config=configs/sana_controlnet_config/Sana_1600M_1024px_controlnet_bf16.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_1600M_1024px_BF16_ControlNet_HED/checkpoints/Sana_1600M_1024px_BF16_ControlNet_HED.pth \
  --json_file=controlnet_request.json \
  --work_dir=output/controlnet \
  --sample_nums=2 \
  --bs=1 \
  --cfg_scale=4.5 \
  --pag_scale=1.0 \
  --thickness=2 \
  --blend_alpha=0.0
```

ControlNet facts:

- Batch size is asserted to be 1 in the native ControlNet script.
- The script derives aspect ratio from the reference/control-map image and
  appends an internal `--ar` suffix to the prompt before calling Sana prompt
  preparation.
- `ref_image_path` invokes `Scribble_HED`; the HED detector checks for
  `ControlNetHED.pth` under the annotator checkpoint directory and downloads it
  if absent. It then moves the detector to CUDA.
- `ref_controlmap_path` bypasses HED detection but still needs image decoding,
  resizing, VAE encode, and CUDA generation.
- `--thickness` changes sketch dilation/erosion. In the Gradio app the range is
  1 to 4; source utility also supports `0` for thinner eroded lines.
- `--blend_alpha > 0` blends the generated image with the control signal for
  debugging/visualization.

## Gradio Image App Launches

Gradio launch commands start interactive servers and load models immediately;
plan them like production GPU jobs.

Default image app:

```bash
DEMO_PORT=15432 python app/app_sana.py \
  --share \
  --config=configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_1600M_1024px_BF16/checkpoints/Sana_1600M_1024px_BF16.pth \
  --image_size=1024
```

Sprint app:

```bash
DEMO_PORT=15432 python app/app_sana_sprint.py \
  --share \
  --config=configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_Sprint_1.6B_1024px/checkpoints/Sana_Sprint_1.6B_1024px.pth \
  --image_size=1024
```

ControlNet app:

```bash
DEMO_PORT=15432 python app/app_sana_controlnet_hed.py \
  --share \
  --config=configs/sana_controlnet_config/Sana_1600M_1024px_controlnet_bf16.yaml \
  --model_path=hf://Efficient-Large-Model/Sana_1600M_1024px_BF16_ControlNet_HED/checkpoints/Sana_1600M_1024px_BF16_ControlNet_HED.pth \
  --image_size=1024
```

4-bit app:

```bash
DEMO_PORT=15432 python app/app_sana_4bit.py --share
```

Gradio expectations:

- The apps bind to `0.0.0.0` and use `DEMO_PORT`, defaulting to `15432`.
- `--share` requests a public Gradio share tunnel; omit it for local-only
  service when a tunnel is not desired or network policy forbids it.
- `ROOT_PATH` can be set for reverse-proxy mounting.
- The default apps may also load ShieldGemma safety checker weights; missing
  safety-checker access can prevent startup even when Sana weights exist.
- If CUDA is unavailable, the apps render CPU warnings and do not provide a
  practical CPU generation path.
