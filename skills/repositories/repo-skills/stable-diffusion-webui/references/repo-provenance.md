# Repo Provenance

## Source Snapshot

- Repository: `AUTOMATIC1111/stable-diffusion-webui` style Stable Diffusion WebUI application checkout
- Commit: `82a973c04367123ae98bd9abdf80d9eda9b910e2`
- Branch: `master`
- Exact tag: `v1.10.1`
- Package version: repository tag v1.10.1
- Remote URL: https://github.com/AUTOMATIC1111/stable-diffusion-webui
- Working tree state: dirty

## Dirty State Summary

This skill was generated from a dirty checkout. Relative changed/untracked paths at generation time:

- `skills/`

## Evidence Paths

Primary repository evidence used to generate this skill:

- `README.md`, `CHANGELOG.md`, `LICENSE.txt`, `CITATION.cff`
- `pyproject.toml`, `requirements.txt`, `requirements_versions.txt`, `requirements_npu.txt`, `requirements-test.txt`, `environment-wsl2.yaml`
- `webui.py`, `launch.py`, `webui.sh`, `webui-user.sh`, `webui.bat`, `webui-user.bat`, `webui-macos-env.sh`
- `modules/cmd_args.py`, `modules/launch_utils.py`, `modules/initialize.py`, `modules/initialize_util.py`, `modules/shared_cmd_options.py`, `modules/shared_options.py`, `modules/options.py`
- `modules/api/api.py`, `modules/api/models.py`, `modules/txt2img.py`, `modules/img2img.py`, `modules/extras.py`, `modules/progress.py`
- `modules/scripts.py`, `modules/script_callbacks.py`, `modules/scripts_postprocessing.py`, `modules/script_loading.py`, `modules/extensions.py`
- `modules/sd_models.py`, `modules/sd_models_config.py`, `modules/sd_vae.py`, `modules/modelloader.py`, `modules/upscaler.py`, `modules/upscaler_utils.py`
- `modules/textual_inversion/`, `modules/hypernetworks/`, `modules/postprocessing.py`
- `scripts/*.py`, `extensions-builtin/*`, `configs/*.yaml`, `textual_inversion_templates/*.txt`, `test/*.py`

## Refresh Cues

Refresh this skill when WebUI changes its launcher flags, `/sdapi/v1/*` routes or Pydantic models, extension callback APIs, model asset discovery, Lora/extra-network behavior, training endpoint parameters, preprocessing/postprocessing scripts, or documented installation requirements.
