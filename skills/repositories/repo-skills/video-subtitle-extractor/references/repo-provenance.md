# Repo Provenance

```yaml
schema: disco.repo-provenance.v1
skill_id: video-subtitle-extractor
source_repo: YaoFANGUK/video-subtitle-extractor
remote_url: https://github.com/YaoFANGUK/video-subtitle-extractor.git
commit: 85746f7df5bf85978fd05f3ca6ce66e321a87a72
branch: main
tag: none-exact-match-recorded
source_working_tree_state_at_extraction: clean before generated skill artifacts
package_version: "2.2.0"
package_metadata: no pyproject/setup metadata; source-run application
python_baseline: "README states Python 3.12+; inspection used Python 3.12 CPU environment"
required_backend_baseline: cpu
optional_backends:
  - cuda-paddlepaddle-gpu
  - directml-onnxruntime
  - other-onnx-providers
```

## Evidence paths

- `README.md`, `README_en.md`
- `requirements.txt`, `requirements_directml.txt`
- `.github/workflows/build-windows-cpu.yml`
- `.github/workflows/build-windows-cuda-10.2.yml`
- `.github/workflows/build-windows-cuda-11.8.yml`
- `.github/workflows/build-windows-cuda-12.6.yml`
- `.github/workflows/build-windows-directml.yml`
- `backend/config.py`, `backend/main.py`
- `backend/tools/ocr.py`, `backend/tools/subtitle_ocr.py`,
  `backend/tools/subtitle_detect.py`, `backend/tools/paddle_model_config.py`,
  `backend/tools/hardware_accelerator.py`, `backend/tools/reformat.py`
- `backend/configs/typoMap.json`, `backend/interface/*.ini`
- `backend/models/V5/*/inference.yml`
- `backend/subfinder/{linux,macos,windows}/` inventory
- `backend/sushi/` modules
- `gui.py`, `ui/` modules
- `test/*.{mp4,flv}` inventory used as native candidate evidence

## Refresh triggers

Refresh this skill when VSE changes its Python/Paddle/PaddleOCR versions,
model directory layout, `PaddleModelConfig` language mapping, GUI task/selection
behavior, `SubtitleExtractor` pipeline, Sushi CLI flags, or backend install
instructions.
