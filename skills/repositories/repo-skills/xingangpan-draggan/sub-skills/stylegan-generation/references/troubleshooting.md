# Generation Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `--class` error | Conditional network has `c_dim != 0` | Provide a valid class index; do not infer it from the filename. |
| `cannot parse 2-vector` | `--translate` is not `a,b` | Use two numeric components such as `0.3,1`. |
| No images written | Missing output permissions, malformed seed range, or invalid pickle | Check the output directory, use `1,2,5-10`, and preflight the model. |
| Renderer says it cannot infer model type | Filename lacks the expected StyleGAN family signal | Rename a copy with `stylegan2`, `stylegan3`, or `stylegan_human`. |
| StyleGAN-Human script imports the wrong module | Root and StyleGAN-Human copies share names (`dnnlib`, `legacy`, `torch_utils`) | Use the bundled builder with an explicit checkout root and the source workflow’s expected working directory. |
| `stylemixing_video.py --help` fails with TensorFlow missing | The source script imports `dnnlib.tflib` at module import time | Install a compatible TensorFlow 1.x environment only if this video path is required, or keep it reference-only. |
| GIF/video creation fails | Missing `ffmpeg`, `moviepy`, `imageio-ffmpeg`, or insufficient disk | Check `ffmpeg -version`, use compatible movie/imageio versions, and estimate frame storage. |
| CPU generation appears hung | High-resolution model and slow CPU path | Reduce seed count/resolution, use a GPU, or treat the run as an expensive job rather than retrying blindly. |
