# PySOT Environment and Install Notes

## When to read

Read this before running PySOT code in a checkout, diagnosing imports, or deciding whether a CPU preflight is enough for a requested workflow.

## Package/import model

PySOT is an older research repository with two important import surfaces:

- `pysot`: the main tracking package (`cfg`, models, trackers, datasets, utilities). The repository's public docs use a checkout/PYTHONPATH workflow for this package.
- `toolkit`: the evaluation toolkit distribution declared by `setup.py`. Building it also compiles the `toolkit.utils.region` extension used by VOT-style overlaps and evaluation code.

A practical development setup normally has both:

```bash
# From a PySOT checkout or with an equivalent editable path registration:
python -c "import pysot, toolkit; import toolkit.utils.region; print('ok')"
```

If `import toolkit` works but `import pysot` fails, the environment probably installed the `toolkit` distribution but did not expose the checkout root to Python.

## Dependency surfaces

Minimum safe inspection and preflight checks need:

- Python with PySOT import path configured.
- PyTorch for model and tracker classes.
- OpenCV (`cv2`) and NumPy for image/tracker utilities.
- YACS and PyYAML for config loading.
- tqdm, matplotlib, colorama, and tensorboardX for toolkit/training/evaluation surfaces.
- Cython plus a C compiler when building `toolkit.utils.region`.

Historical PySOT docs were tested around Python 3.7, PyTorch 0.4.1, CUDA 9.0, and Nvidia GPUs. Modern Python/PyTorch environments can be useful for safe inspection and config/model construction, but do not treat them as proof that the original full benchmark or training scripts are reproducible without adaptation.

## Safe preflight versus full workflows

Safe checks:

```bash
python scripts/check_env.py --repo-root <pysot-checkout>
python scripts/check_env.py --repo-root <pysot-checkout> --config <config.yaml> --model-smoke
```

These checks import modules, optionally merge a config, and optionally instantiate `ModelBuilder`/`build_tracker` on CPU. They do not load snapshots, open video, download datasets, run training, or evaluate metrics.

Full workflows require additional user assets:

- Demo/inference: config, snapshot, video/webcam/image folder, OpenCV display or headless adaptation.
- Benchmark test: config, snapshot, benchmark dataset tree, result-write directory, and CUDA for the unmodified source script path.
- Evaluation: tracker result files plus benchmark dataset JSON sidecars and images.
- Training: cropped training datasets, annotation JSONs, pretrained backbone weights, CUDA, distributed launch settings, and enough time/disk.

## Build notes for `toolkit.utils.region`

If the region extension build fails with Cython errors around `c_region.pxd`, `region_bounds`, `region_polygon`, or missing Cython during isolated builds:

1. Install Cython in the target environment.
2. Prefer a legacy Cython release compatible with the repository extension, for example `Cython<3`.
3. Build/install the repository with build isolation disabled only in a private or controlled environment if the isolated build cannot see Cython.
4. Verify with:

   ```bash
   python -c "from toolkit.utils.region import vot_overlap; print(vot_overlap([0,0,10,10], [0,0,10,10], (20,20)))"
   ```

## Backend expectations

- CPU is enough for import checks, config validation, model construction, result-layout validation, and most reference reasoning.
- CUDA is required for the unmodified source benchmark/training paths that call `.cuda()` directly.
- A visible GPU is not enough: the Python, PyTorch wheel, CUDA runtime, driver, and GPU architecture must be compatible.
- PySOT's historical CUDA stack may not match modern GPUs. If a user needs exact paper-era reproduction, ask for their target environment and accept that dependency pinning may require an older host/container.
