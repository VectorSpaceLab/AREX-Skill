# Repo provenance

## Source snapshot

- Repository: `jianchang512/stt`
- Remote URL: `https://github.com/jianchang512/stt.git`
- Commit: `0df3151d040c8c8becf4ed07b0f1c373163663ae`
- Branch: `main`
- Exact tag at commit: none observed
- Checkout type: shallow Git checkout
- Source working tree before generated skill outputs: clean

## Version markers

- `version.json`: `v0.0.94` / `version_num` 94
- Runtime library marker: `stslib.VERSION = 100`, `stslib.version_str = "v0.1"`

The version markers disagree. Preserve this as a refresh signal rather than choosing one as the only truth.

## Evidence paths used

- `README.md`
- `docs/en/README_EN.md`
- `docs/pt/README_pt-BR.md`
- `requirements.txt`
- `set.ini`
- `start.py`
- `stslib/__init__.py`
- `stslib/cfg.py`
- `stslib/tool.py`
- `templates/index.html`
- `run.bat`
- `test.py`
- `testcuda.py`
- `version.json`

## Environment-inspection baseline

The private inspection environment used Python 3.11 and installed the runtime requirement set. It verified `faster-whisper`, `ctranslate2`, `torch`, Flask/gevent, OpenCC, ffmpeg/ffprobe, and optional CUDA visibility. Do not copy the private environment path into public operating instructions.

## Refresh guidance

Refresh this skill when any of these change materially:

- Route names or request/response shapes in the Flask app.
- `set.ini` keys or how they are passed into `WhisperModel`.
- Model-list defaults or model directory semantics.
- Dependency versions, Python support, or CUDA/CTranslate2 requirements.
- Browser upload/export behavior.
