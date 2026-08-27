# Cross-Cutting Troubleshooting

Use this root reference for issues that span multiple pytorch-yolo-v3 workflows. Route workflow-specific details to the nearest sub-skill when the problem is clearly about cfg/model construction, still-image inference, or video/camera demos.

## Start with safe checks

Run the bundled root preflight to verify dependencies and optional checkout imports without weights, downloads, GUI, video, camera, or inference:

```bash
python scripts/check_environment.py
python scripts/check_environment.py --repo-root <repo-root> --check-files
```

Then route deeper:

- Config, class names, unsupported cfg blocks, or weight-format compatibility: [../sub-skills/model-and-config/SKILL.md](../sub-skills/model-and-config/SKILL.md).
- Still-image preprocessing, postprocessing, no-weight smoke checks, and detection launcher commands: [../sub-skills/image-detection/SKILL.md](../sub-skills/image-detection/SKILL.md).
- Video, webcam, fp16, display/camera, and demo parser pitfalls: [../sub-skills/video-camera-demos/SKILL.md](../sub-skills/video-camera-demos/SKILL.md).

## Common root-level failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `cv2`, `numpy`, `pandas`, `PIL`, or `matplotlib` | The user's Python environment is missing runtime dependencies for the script-oriented repo. | Install the missing dependency in the user's environment. Use `scripts/check_environment.py` to confirm imports before loading weights or opening data. |
| Top-level repo modules such as `darknet`, `util`, `preprocess`, or `bbox` do not import | The user is not running from a checkout/source tree or has not put the repo root on `PYTHONPATH`. | Use bundled helpers with `--repo-root <repo-root>` so they add the user's checkout explicitly. For direct user commands, run from the user's checkout root or configure imports deliberately. |
| User asks for `pip install pytorch-yolo-v3` or package metadata | This repository has no package metadata or console entry points in the inspected baseline. | Treat it as a source/script repository. Use a local checkout/source tree plus installed dependencies instead of claiming distribution metadata. |
| README mentions Python 3.5 and PyTorch 0.4 | The upstream code is legacy and uses `Variable`, `.data`, and old PyTorch idioms. | Do not assume modern compatibility without checks. The generated helpers are intended for safe inspection; actual model inference should be verified in the target environment. |
| Full detection fails because `yolov3.weights` is missing | The repo does not bundle Darknet weights and defaults to a local `yolov3.weights` path. | Ask the user for a local weights file. Do not download weights automatically. Use no-weight smoke helpers when the task is environment or pipeline validation. |
| CUDA behavior differs from CPU behavior | Normal inference uses `torch.cuda.is_available()` to choose CUDA automatically, while some helper paths also take explicit CUDA flags. Optional fp16 requires CUDA. | Verify CPU and CUDA separately when both matter. Use `--expect-cuda` in the root preflight only when the user explicitly requires CUDA. |
| Headless server problems | Video/camera demos call OpenCV GUI functions; camera demo opens device 0. | Do not run full video/camera demos as default validation. Use video/camera parser helpers and route non-interactive image inference to the image-detection sub-skill. |
| User asks about training | The inspected repo README states the code only contains the detection module. | Do not invent training instructions. Treat training/fine-tuning as out of scope unless the user's checkout adds verified training code and the skill is refreshed or extended. |

## Stop conditions

Stop and ask for user input before:

- downloading large external weights or datasets;
- executing a full inference run that writes user outputs;
- opening a GUI window, webcam, or video capture;
- modifying the user's checkout to patch demo bugs or add headless export;
- claiming CUDA/fp16 performance or correctness without a user-approved run on the target hardware.
