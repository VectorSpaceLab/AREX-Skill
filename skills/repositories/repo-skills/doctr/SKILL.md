---
name: doctr
description: "Use python-doctr (docTR) for OCR/KIE inference, document
  IO/export, model customization, datasets/training/evaluation, CLI helpers,
  deployment, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# docTR repo skill

Use this skill when a task involves **python-doctr / docTR**: document OCR, key information extraction, text detection/recognition, layout or table parsing, docTR datasets, model customization, command-line OCR, optional deployment surfaces, or docTR-specific errors.

This is a router. Keep detailed work in the linked sub-skills and references.

## Quick install and import check

Typical install commands:

```bash
pip install python-doctr
pip install "python-doctr[viz,html,contrib]"  # only when visualization, HTML input, or contrib ONNXRuntime helpers are needed
```

Minimal import/metadata check:

```bash
python - <<'PY'
from importlib.metadata import version
import doctr
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
print("python-doctr", version("python-doctr"), "doctr", doctr.__version__)
print(DocumentFile, ocr_predictor)
PY
```

Run [scripts/doctr_env_check.py](scripts/doctr_env_check.py) for a safe package/CLI/backend diagnostic before debugging installation, optional extras, CUDA/MPS, or entry-point problems.

## Route by task

| User task | Read |
|---|---|
| End-to-end OCR or KIE with `ocr_predictor` / `kie_predictor`, rotation/layout/table flags, device/batch choices, or output sanity checks | [sub-skills/core-ocr-and-kie/SKILL.md](sub-skills/core-ocr-and-kie/SKILL.md) |
| Loading PDFs/images/URLs/arrays; interpreting `Document`, `Page`, `KIEDocument`, reading order, JSON/text/XML/Markdown/HTML exports, or table grids | [sub-skills/document-io-and-exports/SKILL.md](sub-skills/document-io-and-exports/SKILL.md) |
| Choosing standalone model factories, supported architectures, custom weights, vocabs/whitelists, Hugging Face Hub, ONNX export, half precision, `torch.compile`, CUDA/MPS | [sub-skills/models-and-customization/SKILL.md](sub-skills/models-and-customization/SKILL.md) |
| Dataset schemas, built-in/custom datasets, synthetic generators, transforms, validation, training/evaluation/latency contracts, metrics, DDP/GPU caveats | [sub-skills/datasets-training-and-evaluation/SKILL.md](sub-skills/datasets-training-and-evaluation/SKILL.md) |
| Installed `doctr-cli`, single-document/batch OCR command helpers, output files, parser defaults, and CLI/script troubleshooting | [sub-skills/cli-and-scripts/SKILL.md](sub-skills/cli-and-scripts/SKILL.md) |
| Optional FastAPI/Streamlit/Docker deployment, `doctr.contrib`, `ArtefactDetector`, optional extras, or Hugging Face publishing/loading | [sub-skills/deployment-and-contrib/SKILL.md](sub-skills/deployment-and-contrib/SKILL.md) |

## Read shared references

- [references/package-overview.md](references/package-overview.md) for package metadata, dependency extras, public modules, CLI entry point, and evidence-backed scope.
- [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, model-cache, file-format, backend, and routing failures.
- [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for another checkout or whether to run `refresh-repo-skill`.

## Operating rules

- Prefer public package APIs and bundled helpers in this skill tree. Do not require future agents to open or run original repo docs, notebooks, scripts, tests, or checkout paths.
- Treat `pretrained=False` as shape/API smoke mode only; random-weight OCR is not meaningful.
- Treat `pretrained=True` and many default backbones as possible first-use network/cache events. Confirm the user's offline/network policy before running them.
- CPU is enough for required package and skill verification. CUDA/MPS are optional acceleration paths unless the user explicitly needs GPU performance, half precision, DDP, or a device-specific issue.
- Install optional extras only for selected tasks: `viz` for `show()`/interactive plotting, `html` for URL/HTML input, `contrib` for ONNXRuntime-backed contrib utilities.
- For training/evaluation, validate labels and run one-sample/one-batch checks before launching long jobs. This skill distills training contracts but does not bundle heavyweight training scripts.
- For services, Docker, Hub push, downloads, credentials, or long-running GPU work, stop and confirm permissions/resources before executing.

## Common first actions

- OCR a file in Python: use `DocumentFile.from_pdf()` or `DocumentFile.from_images()`, build `ocr_predictor(pretrained=True)`, run `result = predictor(doc)`, then inspect `result.render()` or `result.export()`.
- Offline API smoke: use the core OCR sub-skill's `ocr_api_smoke.py` with no pretrained weights.
- CLI JSON OCR: use `doctr-cli --input_path INPUT --output results.json` when model downloads are allowed; use the bundled CLI helper with `--no-pretrained` only for parser/API smoke.
- Validate custom labels: use `sub-skills/datasets-training-and-evaluation/scripts/validate_doctr_labels.py` before training or evaluation.
- Diagnose install/backend: run `scripts/doctr_env_check.py --json`.
