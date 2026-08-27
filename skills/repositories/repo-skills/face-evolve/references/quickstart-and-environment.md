# Quickstart and Environment

## When to read

Read this before running a face.evoLVe workflow, especially when a task mentions install, imports, Python versions, CUDA, PaddlePaddle, `bcolz`, checkpoints, or data layout.

## Source-style repository expectations

face.evoLVe is a script/source checkout rather than a packaged Python distribution. In this snapshot there is no `pyproject.toml`, `setup.py`, `setup.cfg`, or requirements file. Future agents should therefore:

1. Create an isolated Python environment.
2. Install only the dependencies for the selected workflow.
3. Pass a target checkout root to bundled helper scripts when they need to import face.evoLVe source modules.
4. Avoid putting the repository root on `PYTHONPATH` for Paddle workflows until PaddlePaddle is already imported; the local `paddle/` directory can shadow the framework package.

Do not treat a successful import of one framework as proof that every training, quantization, or deployment path is ready. Full training and deployment need external data/model artifacts.

## Minimum workflow dependency groups

| Workflow | Core packages | Extra artifacts/backend |
| --- | --- | --- |
| Face alignment | Python, NumPy, Pillow, OpenCV, SciPy, Torch/TorchVision, tqdm | A target checkout with alignment helper modules and MTCNN `.npy` weights, or an equivalent packaged copy. CPU is enough for small checks. |
| Data preparation | Python stdlib for bundled validators; optional `bcolz`, NumPy for validation pair inspection | ImageFolder-style class directories; external public datasets are not bundled. |
| PyTorch training/components | PyTorch, TorchVision, NumPy, Pillow, OpenCV, SciPy, scikit-learn, matplotlib, tensorboardX, bcolz, tqdm | Large training/validation datasets; checkpoints/log dirs; CUDA recommended for real training. |
| Feature extraction/verification | PyTorch, TorchVision, OpenCV, Pillow, NumPy, SciPy, scikit-learn | A trained backbone checkpoint; aligned images or ImageFolder root; CPU works for small extraction but may be slow. |
| Paddle workflows | PaddlePaddle, PaddleSlim for QAT/quantization, OpenCV, NumPy, Pillow, tqdm, requests | Identity-folder data for training; exported `.pdmodel/.pdiparams`; `.nb` model for Paddle Lite; GPU or edge runtime for deployment demos. |

The README documents legacy-era versions such as Python 3.7, PyTorch 1.0, MXNet 1.3.1, TensorFlow 1.12, OpenCV 3.4.5, `bcolz` 1.2.0, tensorboardX 1.6, and PaddlePaddle 2.1.0. Modern smoke checks may require compatibility repairs; do not downgrade a user environment blindly.

## Safe setup pattern

Use a private environment and install only what the selected route needs. For a CPU inspection/debugging environment, a typical modern package set is:

```bash
python -m pip install numpy scipy scikit-learn pillow opencv-python tqdm tensorboardX matplotlib
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install paddlepaddle paddleslim requests
```

For validation workflows that import `bcolz`, keep NumPy old enough for the installed `bcolz` build or use a maintained replacement after checking the target code. If `bcolz` fails with `np.bool`, use an environment where `bcolz` and NumPy are compatible.

## Smoke checks

Run the root helper first when the task starts from an unknown host:

```bash
python scripts/check_face_evolve_env.py --check torch --check data
```

If the user has a local face.evoLVe checkout and wants component checks, pass it explicitly:

```bash
python scripts/check_face_evolve_env.py --repo-root <face-evolve-checkout> --check torch --check paddle
```

Then route to the focused sub-skill and run its nearest helper:

- `sub-skills/data-preparation/scripts/check_image_folder.py --root <identity-root> --min-num 1`
- `sub-skills/pytorch-training/scripts/inspect_pytorch_components.py --repo-root <face-evolve-checkout> --backbone IR_50 --batch-size 2`
- `sub-skills/paddle-workflows/scripts/inspect_paddle_components.py --repo-root <face-evolve-checkout> --backbone IR_50 --batch-size 2`
- `sub-skills/feature-extraction-verification/scripts/evaluate_pairs.py --embeddings-npy <emb.npy> --issame-npy <issame.npy>`

## Backend policy

- CPU checks are acceptable for import, shape, parser, data-layout, and metric validation.
- CUDA is optional but usually required for practical full training. Verify `torch.cuda.is_available()` and device IDs before setting `MULTI_GPU=True` or using non-empty `GPU_ID` lists.
- Paddle Inference and Paddle Lite demos are artifact/runtime workflows. Do not start them until exported model files, face database images, demo video or stream input, fonts, and the correct runtime backend are available.
