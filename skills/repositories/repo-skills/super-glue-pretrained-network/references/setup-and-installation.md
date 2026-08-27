# Setup and Installation

## Purpose

Read this when preparing a Python environment, diagnosing imports, deciding CPU versus CUDA, or explaining why this repository behaves differently from a normal pip package.

## Repository shape

SuperGluePretrainedNetwork is a source-only research release. It has no `pyproject.toml`, `setup.py`, or console-entry-point metadata. The public import root is the top-level `models/` package inside a checkout or equivalent source distribution.

Expected runtime files:

```text
models/
  matching.py
  superpoint.py
  superglue.py
  utils.py
  weights/
    superpoint_v1.pth
    superglue_indoor.pth
    superglue_outdoor.pth
demo_superglue.py
match_pairs.py
assets/                 # sample images, pair manifests, paper split manifests
```

The generated skill does not bundle the large `.pth` checkpoints. Use a repository/source distribution that includes the release weights.

## Dependencies

The README documents:

- Python 3.5 or newer
- PyTorch 1.1 or newer
- OpenCV 3.4 or newer; OpenCV 4.1.2.30 was recommended by the release for GUI keyboard interaction
- Matplotlib 3.1 or newer
- NumPy 1.18 or newer

A practical modern install command is:

```bash
python -m pip install "numpy<2" torch matplotlib opencv-python
```

Prefer NumPy 1.x for the unmodified release code. The evaluation helper calls `np.trapz`, which is absent in some NumPy 2.x builds; if `match_pairs.py --eval` fails with `AttributeError: module 'numpy' has no attribute 'trapz'`, downgrade to a NumPy 1.x release or patch the source to use `np.trapezoid`.

For headless servers, `opencv-python-headless` may be easier for batch matching and smoke checks, but the interactive demo window requires GUI-enabled OpenCV.

## Import model

Because the repository is not packaged, direct Python code must make the checkout root importable before using `models.*`:

```bash
cd <superglue-repo-root>
python - <<'PY'
from models.matching import Matching
print(Matching)
PY
```

Alternatively, add the checkout root to `PYTHONPATH` or pass `--repo-root` to the bundled skill helpers, which insert that root into `sys.path` internally.

Do not expect `pip show SuperGluePretrainedNetwork` or `python -m superglue` to work; there is no distribution metadata or module entry point.

## Environment check

From this generated skill directory, run:

```bash
python scripts/check_superglue_environment.py --repo-root <superglue-repo-root>
```

The checker validates:

- Python dependency imports: `torch`, `cv2`, `numpy`, `matplotlib`
- `models.matching`, `models.superpoint`, `models.superglue`, `models.utils`
- required checkpoint files under `models/weights/`
- optional CUDA visibility through PyTorch

Use the sub-skill helpers for deeper checks:

```bash
python sub-skills/programmatic-api/scripts/inspect_superglue_api.py --repo-root <superglue-repo-root>
python sub-skills/programmatic-api/scripts/run_matching_api_smoke.py --repo-root <superglue-repo-root> --device cpu
python sub-skills/pair-matching-evaluation/scripts/validate_pair_file.py --pair-file <pairs.txt> --input-dir <images_dir>
```

## CPU and CUDA

The repository scripts choose:

```python
device = "cuda" if torch.cuda.is_available() and not opt.force_cpu else "cpu"
```

Use CPU for portable validation and small smoke tests:

```bash
python match_pairs.py ... --force_cpu
python demo_superglue.py ... --force_cpu --no_display
```

CUDA is optional acceleration. It is not required to validate the core workflow, but it matters for large images, many pairs, high `max_keypoints`, or interactive performance.

## OpenCV GUI caveat

The release notes mention best keyboard interaction with OpenCV 4.1.2.30 and warn that some newer OpenCV builds or Mac builds can have GUI issues. For remote servers:

- prefer `--no_display`;
- use output directories instead of GUI preview;
- use batch or headless smoke helpers before trying webcam/IP inputs.

## License caution

The repository license is for noncommercial research use. Treat code, pretrained weights, derivatives, and generated results according to that license and any institutional policy that applies to the work.
