# Cross-Cutting Troubleshooting

## Import or install fails

| Symptom | Likely cause | Next step |
|---|---|---|
| `ModuleNotFoundError: lightly` | Package is not installed in the active Python environment. | Install with `pip install lightly`, then run `python scripts/check_lightly_environment.py --components import`. |
| PyTorch or Torchvision import errors | Python/PyTorch wheel mismatch, unsupported Python version, or broken GPU wheel. | Verify `python --version`, `python -m pip check`, and a tiny `import torch, torchvision`; prefer a PyTorch-supported Python version. |
| TIMM-backed classes are missing | Optional TIMM extra is not installed. | Install `pip install "lightly[timm]"` only when using TIMM/ViT-style modules. |
| Video dataset errors mention PyAV or video backend | Optional video extra or system libraries are missing. | Install `pip install "lightly[video]"` and verify PyAV before claiming direct video support. |

## Training or CLI writes unexpected artifacts

Lightly CLI training/embedding commands can create checkpoints, embeddings CSVs, Hydra output directories, and environment-variable side effects. Before executing them:

1. Validate the data folder with the CLI/data sub-skill helper.
2. Build the exact command with the command-builder helper.
3. Set explicit output/checkpoint/Hydra paths when reproducibility matters.
4. Confirm runtime budget, backend, and cleanup policy.

## Backend confusion

- A CPU package import is enough for base API inspection but not proof of GPU/distributed training.
- Use CUDA/MPS/ROCm only when the user asks for accelerator behavior or a training plan requires it.
- For distributed losses, set `gather_distributed=True` only inside an initialized `torch.distributed` process group.
- Lightning distributed runs can fail because of spawn/import behavior, fixed rendezvous ports, or worker counts; read the training and maintenance sub-skills before running DDP.

## Data/config confusion

- Lightly image folders may be flat unlabeled folders or class-subdirectory layouts. Empty folders and unsupported extensions should be caught before training.
- `lightly-crop` uses YOLO-style labels: one `.txt` per image, each row `class x_center y_center width height` with normalized coordinates.
- Hydra CLI overrides use keys such as `input_dir`, `loader.batch_size`, `trainer.max_epochs`, `collate.input_size`, `checkpoint`, `label_dir`, `output_dir`, and `crop_padding`. Misspellings may silently change the task or fail late; use the bundled command builder.

## When to stop

Stop and ask for user approval before running commands that download datasets/checkpoints, train for multiple epochs, use GPUs for extended time, write large embeddings/checkpoints, regenerate tracked notebooks, run full docs/test suites, or publish/release artifacts.
