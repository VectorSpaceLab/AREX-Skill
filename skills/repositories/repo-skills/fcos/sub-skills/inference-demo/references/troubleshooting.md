# Inference and Demo Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AssertionError: only 3-channel images are supported` | Input image is grayscale, RGBA, or has unexpected dimensions. | Convert to RGB/BGR 3-channel first; use `prepare_image_for_fcos.py` to validate before detector construction. |
| Very wrong colors or poor detections | RGB/BGR channel order was flipped incorrectly. | Use OpenCV arrays directly as BGR; flip PIL/skimage/imageio RGB arrays once before `detect`. |
| `ImportError: cannot import name '_C'` | FCOS extension missing. | Use root troubleshooting and rebuild with a compatible PyTorch/CUDA/compiler stack. High-level inference cannot be verified without this. |
| `torch._six` or `_download_url_to_file` error | Modern PyTorch API drift. | Use an older supported PyTorch stack for this legacy package or patch intentionally in a maintenance task. |
| Weight download failure | The selected model uses a remote pretrained URL. | Download weights explicitly if allowed, then use lower-level config/weight workflows or a patched cache path. Do not retry indefinitely in automation. |
| OpenCV display hangs or fails | Headless environment, no X server, or webcam/display unavailable. | Avoid `show_bboxes` and GUI demos; serialize detection dictionaries or write rendered images to disk. |
| CUDA out of memory | Image/model too large or insufficient free memory. | Use a smaller MobileNet model, CPU-only for testing, reduce image size, or move to training/evaluation config overrides for batch-size changes. |
