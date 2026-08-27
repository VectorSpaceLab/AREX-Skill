# OpenMed package map

Read this when you need to choose the right OpenMed module, CLI family, extra,
or sibling sub-skill.

## Main public surfaces

| Surface | Use for | Owned by |
| --- | --- | --- |
| `openmed.analyze_text` | Clinical/biomedical token-classification NER with optional sentence segmentation and context metadata | `clinical-extraction-grounding` |
| `openmed.extract_pii`, `openmed.deidentify`, `openmed.reidentify` | PHI/PII detection, masking/removal/replacement/hash/date shifting, reversible mappings | `deidentification-privacy` |
| `openmed.processing.BatchProcessor`, `process_batch`, `redact_dataset` | Batch text/file/dataset processing and progress/checkpoint patterns | `deidentification-privacy` for privacy; `clinical-extraction-grounding` for NER |
| `openmed.core.ModelLoader`, `load_model`, `OpenMedConfig` | Model loading, backend selection, local cache configuration | `model-runtimes-mobile` |
| `openmed.core.model_registry`, `openmed.core.hf_hub` | Model catalog, aliases, size estimates, prefetch/cache management | `model-runtimes-mobile` |
| `openmed.clinical.*` | Clinical context, sections, labs, medications, relations, timelines, grounding, codeable concepts | `clinical-extraction-grounding` |
| `openmed.structured.*`, `openmed.risk.*` | Structured release privacy, quasi-identifiers, k-anonymity/l-diversity/DP/risk reports | `structured-risk-evaluation` |
| `openmed.eval.*`, `openmed.compliance.*` | Leakage gates, metrics, certification evidence, audit/compliance artifacts | `structured-risk-evaluation` |
| `openmed.interop.*` | FHIR, OMOP, HL7 v2, C-CDA, OpenMRS, adapters, framework tools, SQL/distributed connectors | `interoperability-serving` |
| `openmed.service.*`, `openmed.mcp.*` | REST/gRPC/MCP app, client, tool registry, agent workflow surfaces | `interoperability-serving` |
| `openmed.multimodal.*` | Documents, OCR, images, DICOM, metadata, layout, redaction projection/fidelity | `multimodal-document-intake` |
| `openmed.mlx`, `openmed.onnx`, `openmed.coreml`, `openmed.torch` | Backend runtimes, conversion/export, device-specific behavior | `model-runtimes-mobile` |

## CLI families

The `openmed` console command routes many workflows:

- Text and privacy: `analyze`, `batch`, `batch-run`, `deid`, `redact-dataset`,
  `pii`, `audit`, `policy`.
- Structured risk and evaluation: `risk`, `compliance`, `benchmark`, `profile`,
  `eval`, `calibrate`, `gates`.
- Interop and terminology: `export`, `fhir`, `icd11`, `omop`, `ground`,
  `grounding`, `cohort`.
- Models and operations: `models`, `registry`, `config`, `airgap`, `doctor`,
  `active-learning`, `verify-pdf`.
- Maintainer release commands exist, but most package-use tasks should avoid
  release mutation unless the user is explicitly maintaining the repository.

Use `sub-skills/interoperability-serving/references/cli-reference.md` for CLI
routing and safe help probes.

## Optional extras by task

Install only the extras needed for the selected task:

| Extra or dependency family | Use when |
| --- | --- |
| `cli` | Rich/Typer-backed CLI UX paths and command help in a minimal runtime |
| `service` | FastAPI/uvicorn/gRPC/GraphQL/OpenTelemetry service surfaces |
| `mcp` | MCP server/tool registry operation |
| `hf` | Hugging Face/Transformers-backed model downloads or tokenizers |
| `gliner` | GLiNER-family zero-shot or token-classification model paths |
| `mlx`, `coreml`, `onnx`, `onnx-runtime`, `openvino`, `awq`, `gptq` | Specific runtime/export/quantization backends |
| `multimodal`, `ocr-paddle` | Document/image/OCR/DICOM intake and real OCR engines |
| `pandas`, `polars`, `duckdb`, `dask`, `spark`, `ray`, `beam`, `kafka`, `cloud` | Table/dataframe/lakehouse/distributed pipelines |
| `fhir`, `openmrs`, `langchain`, `haystack`, `llamaindex`, `agents`, `spacy` | External framework/server/integration adapters |
| `grounding`, `scispacy`, `quickumls` | Terminology/grounding helpers; restricted vocabularies remain user-supplied |
| `zh`, `indic`, `lid`, `yasbd` | Language-specific segmentation, normalization, or sentence backends |

Avoid broad `dev`, docs, training, GPU, OCR, and distributed extras unless the
user-selected workflow requires them.

## Data and privacy boundaries

- Bundled tests and examples are synthetic; keep new examples synthetic too.
- DUA/restricted datasets and terminology must not be committed or bundled.
- Raw PHI should not be logged, cached to disk, written into golden files, or
  pasted into agent prompts.
- Audit artifacts should contain offsets, hashes, provenance, risk scores, and
  summaries rather than plaintext identifiers.
