---
name: conversion-cli-api
description: "Convert documents with Marker through safe CLI and Python API workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Marker conversion CLI/API

Use this sub-skill when a user needs local document conversion with Marker: single files, folders, chunked multi-GPU runs, table-only conversion, OCR-only conversion, output parsing, or Python API examples.

## Quick route

- For one file, use `marker_single` with `--output_format`, `--page_range`, `--output_dir`, and conversion flags. See [CLI reference](references/cli-reference.md).
- For a folder, use `marker` with the same common options plus `--workers`, `--skip_existing`, `--max_files`, `--chunk_idx`, and `--num_chunks`. See [CLI reference](references/cli-reference.md).
- For multi-GPU shell orchestration, use `marker_chunk_convert` only when the installed environment and GPU topology are ready. See [chunk conversion](references/cli-reference.md#chunked-multi-gpu-folder-conversion).
- For programmatic conversion, use `PdfConverter`, `TableConverter`, or `OCRConverter` with `create_model_dict`, `ConfigParser`, `text_from_rendered`, and `save_output`. See [Python API](references/python-api.md).
- For output interpretation, metadata, images, JSON trees, or chunks, see [output formats](references/output-formats.md).
- For install, device, worker, page range, converter class, optional dependency, and debug failures, see [troubleshooting](references/troubleshooting.md).

## Core commands

```bash
marker_single input.pdf --output_format markdown --output_dir output
marker_single input.pdf --page_range "0,5-10" --disable_image_extraction --output_format json --output_dir output
marker input_folder --output_format json --page_range "0,5-10" --skip_existing --workers 2 --output_dir output
marker_single input.pdf --converter_cls marker.converters.table.TableConverter --force_layout_block Table --output_format json
marker_single input.pdf --converter_cls marker.converters.ocr.OCRConverter --keep_chars --output_dir output
```

Conversion can load models and consume CPU/GPU/VRAM. For planning, environment checks, or CI smoke tests, run [scripts/marker_cli_smoke.py](scripts/marker_cli_smoke.py); it only calls `--help` on installed console scripts.

## Python pattern

```python
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import save_output, text_from_rendered

options = {"output_format": "json", "page_range": "0,5-10", "disable_image_extraction": True}
config = ConfigParser(options)
converter = PdfConverter(
    artifact_dict=create_model_dict(),
    config=config.generate_config_dict(),
    processor_list=config.get_processors(),
    renderer=config.get_renderer(),
    llm_service=config.get_llm_service(),
)
rendered = converter("input.pdf")
text, extension, images = text_from_rendered(rendered)
save_output(rendered, "output/input", "input")
```

For a runnable guarded template, copy or adapt [scripts/marker_conversion_skeleton.py](scripts/marker_conversion_skeleton.py). It requires a real input path and never starts conversion just by being imported.

## Stay in scope

- Route LLM credentials, `--use_llm`, `--llm_service`, structured extraction, and LLM-specific processors to the `llm-extraction-services` sub-skill.
- Route custom processors, renderers, providers, converter internals, config crawling, and schema extension to the `configuration-extension` sub-skill.
- Route `marker_server`, `marker_gui`, `marker_extract`, FastAPI clients, Streamlit apps, and Modal deployment to the `server-deployment` sub-skill.
