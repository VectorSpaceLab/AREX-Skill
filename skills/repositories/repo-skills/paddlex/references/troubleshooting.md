# PaddleX cross-cutting troubleshooting

Use this for package, CLI, dependency, backend, and routing failures that are not specific to one sub-skill.

## Import failures

Symptoms:

- `ModuleNotFoundError: No module named 'paddlex'`
- `ModuleNotFoundError: No module named 'paddle'`
- import succeeds but model execution fails immediately

Actions:

1. Confirm the active Python is the intended environment.
2. Install PaddlePaddle before running real model execution.
3. Install PaddleX with the needed domain extras.
4. Run `python scripts/check_paddlex_install.py`.
5. If only docs/config inspection is needed, avoid installing deployment/GPU/server plugins.

## CPU/GPU confusion

- CPU PaddlePaddle can import and run CPU tensors but cannot satisfy `device="gpu:0"` or HPI GPU.
- A physical NVIDIA GPU does not prove the installed PaddlePaddle wheel is GPU-enabled.
- Check:

```python
import paddle
print(paddle.__version__, paddle.is_compiled_with_cuda())
```

Use CPU as a baseline smoke, then move to GPU only after the wheel/backend stack is verified.

## CLI routing confusion

The `paddlex` CLI groups several unrelated workflows:

- `--install` for plugin/repo installation.
- `--pipeline`, `--input`, `--save_path`, `--get_pipeline_config` for pipeline prediction/config export.
- `--serve` for pipeline serving.
- `--paddle2onnx` for conversion.

If the user asks for module training/evaluation/export, use the self-contained `sub-skills/modules/scripts/run_module_smoke.py --config module_config.yaml --mode ...` patterns from `sub-skills/modules/`, not `--pipeline`.

## Optional dependency gaps

Match dependency extras to capability:

- images/CV: OpenCV, pycocotools, faiss-cpu for retrieval.
- OCR/document: OCR/document dependencies and PDF/table utilities.
- time series: scikit-learn/joblib/calendar utilities.
- speech: soundfile/text normalization utilities.
- video: decoder/codec stack.
- VLM/GenAI: multimodal dependencies, server/client plugins, model downloads, and possibly GPU.

Do not solve an optional dependency error by installing all plugins unless the user requested broad deployment coverage.

## Downloads, credentials, and services

Many PaddleX pipelines and model APIs can download official weights or sample assets. Some document/translation/VLM workflows require remote LLM services or a GenAI server.

Before running such workflows, confirm:

- downloads are allowed.
- cache/storage locations are acceptable.
- credentials or server URLs are available when required.
- runtime and GPU memory budgets fit the selected model.

## Source-checkout leakage

When using this skill, never point the user to a script, config, or docs file in the original PaddleX checkout. Use the bundled references and scripts in this skill. If a user has a separate checkout, treat it as a source of local configs/data only after checking staleness against `repo-provenance.md`.
