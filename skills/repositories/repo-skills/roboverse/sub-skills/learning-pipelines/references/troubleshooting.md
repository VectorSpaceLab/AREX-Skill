# Learning Pipeline Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Import fails for an IL/VLA policy | The selected policy's private requirements are not in the base package extras or versions conflict | Identify the exact policy and install its documented dependency set in an isolated environment; keep the base CPU utilities separate. |
| `No GPU available` or CUDA import failure | Config requests CUDA, but the torch build/driver/device is unavailable | Probe `torch.cuda.is_available()` in the target environment; set CPU only for a CPU-valid smoke, or install a compatible backend. Do not label CPU training as GPU verification. |
| Dataset loader returns empty or shifted episodes | Wrong format version, split, action frame, timestamps, or empty-trajectory handling | Run a tiny schema validator; inspect one episode and expected keys/shapes; fix conversion metadata before training. |
| Loss is NaN or validation diverges | Invalid normalization, NaN input, mixed units, action range mismatch, or too-high learning rate | Check finite tensors and per-key ranges; freeze/evaluate normalizers correctly; compare one batch on CPU; only then tune. |
| Resume produces different behavior | Missing normalizer/optimizer/config state or changed task/camera/action order | Compare checkpoint keys and training identity; restore preprocessing and architecture together; reject incompatible resumes. |
| Evaluation action has wrong dimensions/range | Training and inference wrappers expose different action order, clipping, or gripper convention | Print action shape/range and task spec; apply the exact unscale/clamp/order path and add a one-step assertion. |
| WandB/model hub/download hangs | Network, credentials, or external model/data are required | Run an offline tiny fixture or disable the integration; never treat a timeout as a model failure and never embed credentials. |
| VLA/renderer process exhausts memory | Model weights, image resolution, batch, or simulator rendering is too large | Start with one environment, low resolution, CPU/tiny batch or a documented memory-saving mode; report hardware limits. |
| Compilation or AMP changes behavior | `torch.compile`, AMP dtype, or backend-specific kernels alter numerical/runtime behavior | Disable compile/AMP for the minimal reproduction; compare finite outputs and re-enable one feature at a time. |
