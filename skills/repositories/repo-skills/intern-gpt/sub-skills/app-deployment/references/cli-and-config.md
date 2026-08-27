# CLI and configuration reference

The InternGPT app launcher is a Gradio service with a small CLI. It builds a `load_dict` from `--load`, creates a `ConversationBot`, then exposes UI tabs selected by `--tab`.

## CLI flags

| Flag | Default | Meaning | Deployment notes |
| --- | --- | --- | --- |
| `--port`, `-p` | `7862` | TCP port used by Gradio. | Commands in this skill often use `3456` for user-facing demos; Docker examples commonly expose `7862`. Keep host/container port mapping consistent. |
| `--debug`, `-d` | off | Bypasses the UI OpenAI-key login check and initializes the agent for debugging. | Do not recommend this for a public service. It does not prove that OpenAI-backed chat calls will work without credentials. |
| `--https` | off | Launches Gradio with TLS files under `certificate/`. | Requires `certificate/cert.pem` and `certificate/key.pem` relative to the application working directory. Browser microphone/voice-assistant use generally needs HTTPS. |
| `--load` | `HuskyVQA_cuda:0,ImageOCRRecognition_cuda:0,SegmentAnything_cuda:0` | Comma-separated direct model/tool classes and devices. | The parser expects each item to look like `<ClassName>_<device>`, for example `HuskyVQA_cuda:0`. |
| `--tab` | `Audio,DragGAN,Image,Video` | Comma-separated UI tab names. | Supported tabs are exactly `Audio`, `DragGAN`, `Image`, and `Video`; enabling a tab does not by itself load the model classes it needs. |
| `--e-mode`, `-e` | off | Memory-saving mode for many wrappers. | Models that implement e-mode move to GPU for work and back to CPU afterward. It saves VRAM but does not eliminate CUDA/checkpoint requirements. |

## `--load` grammar

Use a comma-separated list of items shaped as:

```text
<ClassName>_<device>[,<ClassName>_<device>...]
```

Examples:

```text
HuskyVQA_cuda:0,SegmentAnything_cuda:0,ImageOCRRecognition_cuda:0
StyleGAN_cuda:0
ActionRecognition_cuda:0,VideoCaption_cuda:0,DenseCaption_cuda:0
```

Rules and gotchas:

- The class name is the part before the first underscore and must match an exported model/tool class.
- The device is the part after the underscore, usually `cuda:0`. Some low-level PyTorch modules may accept other devices, but the app and dependencies are primarily CUDA-oriented.
- Duplicate classes collapse to the last value because the app stores them in a dictionary; treat duplicates as a plan error or warning.
- Template classes should not appear directly in `--load`; they are auto-created only after their prerequisites are loaded.
- Some exported classes are not safe direct CLI entries in the current app because their constructors do not match the app's `device, e_mode` call pattern.

## Direct app-loadable exported classes

These exported classes match the app's direct constructor pattern and are the safest candidates for `--load`:

```text
ActionRecognition
Anything2Image
CannyText2Image
DenseCaption
HuskyVQA
Image2Canny
Image2Hed
Image2Line
Image2Scribble
ImageOCRRecognition
LDMInpainting
ReplaceMaskedAnything
ScribbleText2Image
SegText2Image
SegmentAnything
StyleGAN
Text2Image
VideoCaption
```

## Exported template-only classes

Do not put these directly in `--load`. The app discovers them after direct models are initialized:

| Template class | Created when these prerequisites are loaded | What it enables |
| --- | --- | --- |
| `ExtractMaskedAnything` | `SegmentAnything` | Extract an object/region from a SAM mask. |
| `ImageText2Image` | `SegText2Image`, `SegmentAnything` | Generate/edit from an image plus text using segmentation. |
| `Audio2Image` | `Anything2Image` | Generate an image from an audio embedding. |
| `Thermal2Image` | `Anything2Image` | Generate an image from a thermal image embedding. |
| `AudioImage2Image` | `Anything2Image` | Generate from audio plus image. |
| `AudioText2Image` | `Anything2Image` | Generate from audio plus text. |
| `GenerateTikTokVideo` | `ActionRecognition`, `VideoCaption`, `DenseCaption` | Compose action, caption, dense captions, OpenAI text, speech, and ffmpeg into a short clip. |

## Other known exported classes

These names are exported by the model package, but the current app launcher passes `e_mode` to every direct `--load` class. Avoid direct `--load` entries for these unless the app code has been patched to support their constructor signatures:

```text
DepthText2Image
HedText2Image
Image2Depth
Image2Normal
Image2Pose
InstructPix2Pix
LineText2Image
NormalText2Image
PoseText2Image
```

## Supported tabs

| Tab | Minimal useful direct loads | Notes |
| --- | --- | --- |
| `Image` | Basic: `HuskyVQA`, `SegmentAnything`, `ImageOCRRecognition`; add generation/editing classes as needed. | Detailed image tool behavior belongs to `../visual-dialogue-tools/SKILL.md`. |
| `DragGAN` | `StyleGAN` | The tab uses the `StyleGAN` model state; there is no separate `DragGAN` entry in the default exported `--load` list. |
| `Audio` | `Anything2Image` for ImageBind generation; microphone voice input also depends on browser HTTPS and the speech model. | Detailed ImageBind generation belongs to `../cross-modal-generation/SKILL.md`. |
| `Video` | `VideoCaption`, `ActionRecognition`, `DenseCaption`; add all three for `GenerateTikTokVideo`. | Detailed video workflows belong to `../video-understanding/SKILL.md`. |

## Static validation workflow

Before recommending a command, run the bundled validator from this sub-skill directory:

```bash
python scripts/validate_load_plan.py \
  --load "StyleGAN_cuda:0" \
  --tab "DragGAN" \
  --https \
  --e-mode
```

The validator does not import the app or model package. It checks grammar, exported class names, direct-load safety, tab names, common tab/load mismatches, template prerequisites, HTTPS certificate expectation, and e-mode caveats.
