# LTX-Video repository provenance

## Source snapshot

- **Repository:** Lightricks/LTX-Video
- **Remote URL:** `https://github.com/Lightricks/LTX-Video.git`
- **Commit:** `4b2d053057623ddd4d0a1d3e9cd28890e9ef487f`
- **Branch:** `main`
- **Distribution:** `ltx-video`
- **Version at snapshot:** `0.1.2`
- **Import root:** `ltx_video`
- **Supported Python:** 3.10 or newer
- **Working-tree note:** `skills/` was untracked while this skill bundle was produced; the source snapshot hash therefore identifies repository code, not the generated skill files.

## Evidence used

The root and leaf skills were distilled from these repository-relative sources:

- `README.md`
- `pyproject.toml`
- `inference.py`
- `configs/*.yaml`
- `ltx_video/inference.py`
- `ltx_video/pipelines/`
- `ltx_video/models/autoencoders/`
- `ltx_video/models/transformers/`
- `ltx_video/schedulers/`
- `ltx_video/utils/`
- `tests/test_inference.py`
- `tests/test_configs.py`
- `tests/test_scheduler.py`
- `tests/test_vae.py`
- `tests/conftest.py`
- `.github/workflows/pylint.yml`
- `.pre-commit-config.yaml`

The bundled model catalog covers the 11 YAML files present under `configs/` at this snapshot. The safe helper scripts are adaptations and summaries; they do not require the original repository and do not include checkpoints or external model code.

## Dependency boundaries

The source package declares core dependencies including PyTorch, Diffusers, Transformers, SentencePiece, Hugging Face Hub, Einops, and timm. Local media inference additionally needs the repository's `inference` extra. FP8 configurations depend on external Q8/FP8 kernels not installed by the base project. Checkpoints, text encoders, prompt-enhancement models, and spatial upscalers can require Hugging Face access and large local caches.

## Refresh rule

Refresh this skill when the checkout moves past the recorded commit, the public `InferenceConfig` or pipeline signatures change, YAML files are added/removed, package extras change, or model/checkpoint guidance in the README changes. Recheck every relative link and rerun only the safe verification tier in `development-and-tests.md` before publishing refreshed guidance.
