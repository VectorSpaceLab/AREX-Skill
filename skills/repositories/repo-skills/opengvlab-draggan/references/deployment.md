# Deployment and launch

## Purpose

Read this when you need to install DragGAN, launch the browser demo, or pick a launch mode for a fresh environment.

## Install pattern

The package metadata names the distribution `draggan` and the repo snapshot is version `1.1.6`.

A safe public install pattern is:

```bash
python -m pip install "draggan==1.1.6"
```

If you are working from a local checkout, an editable install is fine too:

```bash
python -m pip install -e .
```

Install a CUDA-enabled PyTorch/TorchVision pair first. The repo docs recommend using Conda or another environment manager for that part so the wheel/build combination matches your GPU driver and CUDA runtime.

## Preflight

Before launching the UI, run the bundled check script:

```bash
python scripts/check_install.py --mode web
```

Use `--mode api` when you only need the library import and API surface.
The bundled launcher runs the same web preflight automatically unless you pass `--skip-preflight`.

## Browser launch

Use the bundled launcher rather than a source checkout path:

```bash
python scripts/launch_web_demo.py --device cuda --ip 0.0.0.0 --port 7860
```

Add `--share` if you want a public Gradio link.

## Docker

The repository also documents a Docker image path. The distilled workflow is:

```bash
docker build -t draggan .
docker run --gpus all -p 7860:7860 draggan
```

## Notebook-style use

If you are working in a notebook or Colab-like environment, use the same preflight and launcher commands in notebook cells instead of relying on a source notebook path.

## Notes

- The verified drag path requires CUDA.
- CPU or MPS launch flags are not a verified editing path in this snapshot.
- The demo saves outputs in `draggan_tmp/` under the current working directory of the launcher process.
- Checkpoint files are resolved separately in `references/checkpoints.md`.
