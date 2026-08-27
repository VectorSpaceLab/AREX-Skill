# Troubleshooting Gradio Inference Apps

Use this reference when a ControlNet 1.0 app fails to launch, inspect, or produce expected outputs.

## Fast Diagnosis Matrix

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| Importing `gradio_canny2image.py` hangs, loads CUDA, or starts a server | App scripts have top-level model loading and `block.launch(...)` | Do not import launch scripts for metadata; run the bundled AST helper. |
| `FileNotFoundError` for `models/cldm_v15.yaml` | Shared model config is missing or command ran from wrong working directory | Check required model layout and run from the checkout root when launching. |
| Missing `models/control_sd15_*.pth` | ControlNet task checkpoint is absent | Identify the app-specific checkpoint from the parameter reference; obtain it before launch. |
| Missing detector checkpoint under `annotator/ckpts` | HED, MiDaS, OpenPose, Uniformer, or related detector weights are absent | Use detector preprocessing guidance; avoid automatic downloads unless authorized. |
| `ModuleNotFoundError: gradio` | Minimal environment does not include Gradio | Install the repository-documented Gradio dependency in the app runtime environment before launching. |
| Gradio API errors such as old `source`, `tool`, or `.style(...)` arguments failing | Gradio version mismatch | Use the repository's environment expectations or adapt UI calls to the installed Gradio version. |
| CUDA unavailable or `torch.cuda` errors | App scripts move model/control tensors to CUDA unconditionally | Use a CUDA-capable environment or adapt the script deliberately; the original apps are not CPU-first. |
| CUDA OOM during model load or sampling | Batch, resolution, detector, or checkpoint memory exceeds GPU capacity | Set `config.save_memory=True`, reduce `num_samples`, reduce `image_resolution`, and lower `detect_resolution` where available. |
| Low VRAM mode still OOMs | Low-VRAM shifting is not guaranteed for all cards/settings | Further reduce batch/resolution or use a larger GPU; do not promise low-VRAM success. |
| Outputs change between runs | `seed=-1` or nondeterministic GPU/runtime behavior | Set a fixed non-negative seed; keep environment and parameters constant. |
| Guess mode ignores prompts or behaves unexpectedly | Guess mode omits control from unconditional conditioning and uses decaying control scales | Lower guidance scale to roughly 3-5 for promptless experiments, tune `strength`, and explain that prompts are optional but still accepted. |
| Canny output too sparse or noisy | Thresholds are poorly matched to the image | Tune `low_threshold` and `high_threshold`; lower thresholds reveal more edges, higher thresholds reduce noise. |
| M-LSD misses lines or over-detects | Value/distance thresholds or detect resolution mismatch | Tune `value_threshold`, `distance_threshold`, and `detect_resolution`. |
| Normal map foreground/background looks wrong | `bg_threshold` mismatch | Adjust `bg_threshold`; compare with the depth app for the same prompt/seed. |
| Network failures while loading detectors | Some annotators contain Hugging Face URL fallback paths | Pre-place required weights under `annotator/ckpts`; do not rely on runtime downloads in restricted environments. |

## Missing Checkpoints And Layout

The launch scripts expect paths relative to the ControlNet checkout root. The shared config is `models/cldm_v15.yaml`; app-specific checkpoints are named `models/control_sd15_canny.pth`, `models/control_sd15_mlsd.pth`, `models/control_sd15_hed.pth`, `models/control_sd15_scribble.pth`, `models/control_sd15_openpose.pth`, `models/control_sd15_seg.pth`, `models/control_sd15_depth.pth`, and `models/control_sd15_normal.pth`.

Detector apps may also require annotator checkpoints. HED/fake scribble use HED, pose uses OpenPose body/hand weights, segmentation uses Uniformer, and depth/normal use MiDaS. Keep detector details in the annotator preprocessing sub-skill.

## Top-Level Side Effects

Treat the app files as executable scripts, not libraries. At import time they can:

- instantiate detector objects,
- call `create_model('./models/cldm_v15.yaml')`,
- call `load_state_dict(..., location='cuda')`,
- move the model to CUDA,
- create `DDIMSampler(model)`, and
- call `block.launch(server_name='0.0.0.0')`.

Use `scripts/extract_gradio_signatures.py` whenever the task is to inspect signatures, controls, or checkpoint references. If the user needs reusable code, copy the relevant `process(...)` logic into a new guarded script and make model loading explicit.

## Output And Seed Issues

Each process function returns a gallery list with the control visualization first, followed by generated samples. Some apps invert the control map for display (`255 - detected_map`), while pose, segmentation, depth, and normal return the detected map directly. When comparing image outputs, ignore the first gallery item if the user only cares about generated samples.

When `seed == -1`, the scripts replace it with `random.randint(0, 65535)`, so the UI slider's larger range does not describe the random replacement range. Use a fixed non-negative seed for comparisons across apps such as depth versus normal.
