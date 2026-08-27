# StyleGAN-Human Manipulation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'paddle'` or `paddleseg` | Alignment path was selected without Paddle/PP-HumanSeg dependencies | Treat alignment as blocked until Paddle/PaddleSeg and exported PP-HumanSeg assets are installed; background whitening does not need these packages. |
| OpenPose model file missing | `body_pose_model.pth` is absent from the expected OpenPose model path | Use the asset checker; place the exact model file in the expected local checkout path only after reviewing its source/license. |
| Alignment skips an image | Multiple people, low-confidence body keypoints, bad crop, or unreadable input | Use one-person, full-body images and inspect segmentation/keypoints; do not force a skipped multi-person photo into PTI. |
| White-background output count is zero | No raw/mask filename pairs or unreadable images | Check matching filenames and image dimensions; run the bundled `bg_white.py` on a tiny known pair before batching. |
| PTI creates no embedding or checkpoint | Missing aligned input, missing e4e weight, bad PTI path config, or missing StyleGAN-Human checkpoint | Verify `input_data_path`, e4e weight, SHHQ checkpoint, output directories, and CUDA before launching the config-driven PTI script. |
| `edit.py` reports unknown attribute | Attribute is not one of the demo names | Use `upper_length` or `bottom_length`; their strengths/layers are defined in the edit configuration. |
| Latent-direction file missing | `latent_direction` directories exist but required files are absent | Use the asset checker; do not create placeholder direction files. Editing needs the real direction/statistics assets. |
| Custom CUDA op fails to build/load | CUDA toolkit/compiler mismatch, missing `CUDA_HOME`, stale torch-extension cache, or incompatible PyTorch/CUDA version | Fix the toolchain and clear stale extension cache only after confirming it is safe. Do not treat a failed extension import as a verified editing path. |
| `real=True` edit fails | PTI latent path or real image path does not correspond to the current fine-tuned checkpoint | Preserve the artifact chain: aligned image, PTI embedding, PTI checkpoint, attribute and strength, final output. |
| InsetGAN cannot find dlib detector/landmarks | Face/body/dlib assets are absent or named differently | Check all InsetGAN assets before execution: body checkpoint, face checkpoint, shape predictor, CNN face detector, LPIPS, CUDA. |
| Video output fails | Missing FFmpeg/moviepy/imageio-ffmpeg or insufficient disk | Verify the media stack and turn off video output for a first image-only run. |
| Generated command imports the wrong `torch_utils` or `legacy` | Root DragGAN and StyleGAN-Human have overlapping module names | Keep the execution context for StyleGAN-Human workflows separate from top-level DragGAN commands; use explicit repo roots and inspect `PYTHONPATH`. |

## Block policy

Alignment, PTI, editing, InsetGAN, and full StyleGAN-Human manipulation are required-CUDA/asset workflows. If a required model, latent direction, third-party dependency, CUDA toolchain, or dataset is absent, record a blocked preflight and ask the user for the missing asset or scope change. Do not downgrade these workflows to CPU-only imports or generic advice.
