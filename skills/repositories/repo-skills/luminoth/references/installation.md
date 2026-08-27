# Installation

## Purpose

Read this when you need to install or smoke-test Luminoth itself before using
one of the workflow sub-skills.

## Verified package facts

- Package name: `luminoth`
- Installed version in the inspected repo snapshot: `0.2.4dev0`
- Public import name: `luminoth`
- Console entry point: `lumi`
- Supported Python range documented by the repo: Python 2.7 and 3.4–3.6
- TensorFlow is required at import time; the package checks for it immediately.
- Optional TensorFlow installation extras exist: `luminoth[tf]` and
  `luminoth[tf-gpu]`
- Optional Google Cloud extras exist: `luminoth[gcloud]`
- FFmpeg is required only when you want video prediction output.

## Recommended installs

From a checkout:

```bash
pip install -e .
```

From PyPI:

```bash
pip install luminoth
```

If you want Luminoth to pull TensorFlow for you, use one of the documented
extras:

```bash
pip install "luminoth[tf]"
pip install "luminoth[tf-gpu]"
```

If you need Google Cloud training helpers:

```bash
pip install "luminoth[gcloud]"
```

## Minimal smoke

Run the safe bundled smoke first:

```bash
python scripts/check_luminoth_install.py
```

If you just need the public CLI help, this is also a valid smoke:

```bash
lumi --help
```

## Common prerequisites

- Install TensorFlow before importing Luminoth.
- Use the GPU TensorFlow build only if you actually need GPU-backed training or
  inference.
- Install FFmpeg at the system level only if you need video prediction output.
- Install the Google Cloud extras only if you plan to use `lumi cloud gc`.

## When this is enough

This reference is only for setup and smoke checks. Once importability is
confirmed, switch to the relevant workflow sub-skill for dataset preparation,
training, prediction, or checkpoint management.
