# Evaluation troubleshooting

Use this reference when a generated LIBERO or CALVIN evaluation command fails, hangs, or produces metrics that do not match the expected benchmark surface.

## Fast triage

1. Confirm the generated command matches the intended benchmark, suite, checkpoint, GPU, Pro flag, and log file.
2. Confirm CUDA works in the active runtime and the selected GPU is visible to PyTorch.
3. Confirm the benchmark-specific external stack is installed: LIBERO for LIBERO suites; CALVIN packages and dataset assets for `calvin_abc`.
4. Confirm the checkpoint directory includes `dataset_statistics.json` and the expected component checkpoint files when loading locally.
5. Inspect the log tail first, then videos/results. Long benchmark runs can produce thousands of lines and many MP4s.

## Common failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: libero` | External LIBERO simulator package is not installed in the runtime. | Install the LIBERO stack and the LIBERO-specific requirements before running a LIBERO suite. The base VLA-Adapter package alone is not enough for benchmark rollouts. |
| `ModuleNotFoundError: calvin_agent` or `calvin_env` | External CALVIN packages are not installed or are not importable. | Install the CALVIN repository packages and ensure the runtime can import CALVIN modules before launching `calvin_abc`. |
| CALVIN cannot find dataset/config files | The evaluator expects a relative `calvin` directory with dataset and model config assets. | Place or symlink CALVIN assets into the expected relative layout, or make an intentional local patch. Do not assume an externally exported `CALVIN_ROOT` overrides the evaluator, because it sets the root internally. |
| `AttributeError: 'NoneType' object has no attribute 'eglQueryString'` | Headless EGL/OpenGL/MuJoCo/pybullet renderer setup is incomplete. | Install system EGL/OpenGL/Mesa development libraries as appropriate for the host, set a headless renderer such as EGL when needed, and verify the GPU driver can create an EGL context. |
| Process appears stuck after a TensorFlow CUDA compatibility warning | TensorFlow may JIT-compile kernels for a newer GPU architecture on first use. | Wait if the process is still consuming GPU/CPU resources. Treat it as a failure only after no progress and no resource activity. |
| cuDNN/cuFFT/cuBLAS factory registration warnings | Mixed TensorFlow/PyTorch imports can register GPU libraries more than once. | Usually benign if imports continue and the evaluator reaches model loading. Do not stop solely on these warnings. |
| `huggingface/tokenizers: The current process just got forked` | Tokenizers parallelism warning after simulator subprocess/fork use. | Usually benign. Set `TOKENIZERS_PARALLELISM=false` in the shell if the warning is noisy or if deadlock is suspected. |
| `Action un-norm key ... not found` | Checkpoint statistics do not contain the suite key expected by the command. | Match the suite to the trained checkpoint. For LIBERO RLDS `_no_noops` checkpoints, run the suite without the suffix, such as `libero_10`; the evaluator can fall back to a `_no_noops` stats key if present. |
| `WARNING: No local dataset_statistics.json` followed by action prediction errors | A local fine-tuned checkpoint is missing normalization statistics. | Add the correct `dataset_statistics.json` from training/checkpoint export, or use a checkpoint directory that already contains it. |
| `Unsupported HF Hub pretrained checkpoint found!` | The helper's Hub component mapping is narrower than the user's model id. | Use a local checkpoint directory containing the action head and proprio projector files, or update the runtime code deliberately after confirming the checkpoint layout. This commonly affects original, CALVIN, or custom checkpoints. |
| Local checkpoint files are modified or backup files appear | The model-loading helper can update local `config.json` and synchronize modeling/configuration files for local checkpoints. | Use a disposable copy of a checkpoint when evaluating experimental code, and keep generated backups until the run succeeds. |
| LIBERO command uses `LIBERO-long-Pro` or another case variant | Path/name case mismatch. | Prefer the canonical checkpoint family name `LIBERO-Long-Pro` unless the actual local directory uses a different case. The suite flag remains `libero_10`. |
| `datasets path ... does not exist` appears in LIBERO logs | LIBERO package cannot find one of its dataset locations. | If rollouts continue, it may be a non-fatal warning while using default initial states. If environment reset or task loading fails, fix the LIBERO asset layout. |
| MoviePy or ffmpeg errors while saving videos | Video writer dependency or codec support is missing. | Install ffmpeg/imageio video support in the runtime, or adjust the evaluator only if the user accepts no-video output. Full published logs include video writing. |
| Disk fills during CALVIN evaluation | CALVIN writes static and gripper MP4s for every subtask in a 1,000-sequence run. | Reserve enough output storage, run a small smoke evaluation only after intentionally modifying the evaluator, or clean old result directories before a full run. |
| CALVIN summary lacks `Average successful sequence length` | Evaluation crashed before final aggregation. | Inspect the first exception above the tail; the final metric is printed only after all assigned sequences finish and `print_and_save` runs. |

## Metric-debugging checklist

- For LIBERO, verify the log reports exactly 500 total episodes before comparing with published success rates.
- For CALVIN, verify the log reports 1,000 sequences and prints chain success rates for 1 through 5 instructions.
- Keep image rotation, JPEG/Lanczos resizing, proprio inclusion, two-image input, gripper normalization, and OpenVLA gripper inversion unchanged for paper-comparable numbers.
- Use `--use_pro_version True` only with a Pro-compatible checkpoint; use `--use_pro_version False` for original/custom action heads that were not built with the Pro action-head layout.
- Prefer a local checkpoint directory for custom or non-Pro runs so the evaluator can find component files deterministically.
- Treat fewer trials, changed max steps, disabled video writing, changed renderer, or changed simulator versions as non-published evaluation variants.
