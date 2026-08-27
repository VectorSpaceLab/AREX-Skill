# Converter patterns for VLMEvalKit benchmarks

Use converters to transform upstream raw data into VLMEvalKit TSVs and image/video cache trees before any model evaluation. The active bundled helper is intentionally small and safe; larger converters are reference patterns because they require network downloads, large archives, external services, or dataset-specific raw trees.

## General converter checklist

1. **Define the target dataset name.** Match the class/preset name that `build_dataset` or `--data-config` will use.
2. **Choose embedded images vs paths.** Prefer `image_path` with relative paths for large/multi-page data; use `image` base64 only when the source benchmark is small or expects embedded images.
3. **Preserve stable ids.** Keep `index` unique and carry source ids such as `question_id`, `doc_no`, `task`, or `source_dataset`.
4. **JSON-encode structured cells.** Use `json.dumps(..., ensure_ascii=False)` for image lists, evidence pages, tags, and nested metadata.
5. **Keep prompt semantics in `question`.** If the dataset needs interleaved media, put `<image token>` / `<image>` markers in `question` and align them with the `image_path` list order.
6. **Validate before writing.** Check required columns, duplicate indices, empty questions, parseable JSON lists, and representative image files.
7. **Separate large side effects.** TSV construction, image archive extraction, and model evaluation should be separate commands.

## Bundled LongDocURL TSV helper

The bundled script is [scripts/build_longdocurl_tsv.py](../scripts/build_longdocurl_tsv.py). It supports:

- Local JSONL mode with `--jsonl` for tiny fixtures or already-downloaded source data.
- Optional Hugging Face dataset download when `--jsonl` is omitted.
- Optional `--limit` for smoke conversion.
- Optional image-path validation with `--image-root`.

Example local fixture conversion:

```bash
python scripts/build_longdocurl_tsv.py \
  --jsonl tiny_longdocurl.jsonl \
  --output LongDocURL.tsv \
  --limit 1
```

Expected TSV columns include `index`, `question_id`, `question`, `answer`, `image_path`, `doc_no`, `total_pages`, `start_end_idx`, `question_type`, `answer_format`, `task_tag`, `evidence_pages`, `evidence_sources`, `subTask`, `detailed_evidences`, and `pdf_path`.

Use `LONGDOCURL_TSV_ROOT` to point the dataset class to the TSV directory and `LONGDOCURL_IMAGE_ROOT` to point it to prepared page images.

## LongDocURL pattern

Source evidence: `scripts/build_longdocurl_tsv.py`, `scripts/prepare_longdocurl_images.py`, and `vlmeval/dataset/longdocurl.py`.

Pattern:

- Input JSONL rows contain `images`, `question`, `answer`, evidence fields, and document metadata.
- `relative_image_path` strips any prefix up to `/pdf_pngs/` so TSV paths are relative to the LongDocURL image root.
- `answer`, `start_end_idx`, `evidence_pages`, `evidence_sources`, and `subTask` are JSON-encoded when structured.
- The dataset class can generate `LongDocURL.tsv` from local JSONL or download JSONL when no TSV exists.
- Image preparation is a separate step; do not hide archive/download work inside a tiny TSV smoke conversion.

## MMLongBench pattern

Source evidence: `scripts/build_mmlongbench_tsv.py`, `scripts/package_mmlongbench_images.py`, and `vlmeval/dataset/mmlongbench.py`.

Pattern:

- Use released VLMEvalKit TSVs as split/order references when rebuilding from raw files.
- Convert task families separately, then join by `(task, source_dataset, question_id)`.
- Preserve published `index` and, for ICL prompts, preserve released exemplar order instead of re-randomizing.
- Store multi-image contexts as JSON-encoded `image_path` lists.
- Keep `task`, `source_dataset`, `mmlb_subset`, `tags`, and `extra_info` columns for evaluator logic and diagnostics.
- Archives must be extracted with path traversal protection.
- Large raw archives and image archives should be opt-in and cacheable; do not run them as part of a small skill verification.

Safe archive extraction pattern:

```python
import os
import os.path as osp

def safe_extract(tar, path):
    root = osp.abspath(path)
    for member in tar.getmembers():
        target = osp.abspath(osp.join(root, member.name))
        if not (target == root or target.startswith(root + os.sep)):
            raise RuntimeError(f'Unsafe path in tar archive: {member.name}')
    tar.extractall(root)
```

## MemLens pattern

Source evidence: `scripts/build_memlens_tsv.py` and `vlmeval/dataset/memlens.py`.

Pattern:

- Flatten conversational sessions into one long `question` string.
- Keep `<image>` tokens in the context when source text already includes them; otherwise insert one token per attached image before the turn text.
- Store corresponding image paths as a JSON-encoded `image_path` list in the same order as tokens.
- Carry `question_id`, `question_type`, and `question_date` for evaluator logic.
- Use `MEMLENS_TSV_ROOT` and `MEMLENS_IMAGE_ROOT` for local TSV/image overrides.

## MaCBench pattern

Source evidence: `scripts/convert_macbench.py`.

Pattern:

- Iterate over many Hugging Face dataset configs and add the config name as `category`.
- Parse each row's nested example payload.
- Replace placeholders in the source question with text entries or `{image}` placeholders.
- Store image data in `image` as base64 when the upstream source already provides data URIs.
- For `target_scores`, create option columns `A`, `B`, ... and set `answer` to the true option labels.
- Preserve numeric tolerance fields such as `relative_tolerance` when evaluators need them.

Because the source converter loads many configs and uses multiprocessing without a tiny built-in limit, keep it reference-only unless a user explicitly authorizes the dataset download.

## OmniMat pattern

Source evidence: `scripts/convert_omnimat.py` and `vlmeval/dataset/omnimat.py`.

Pattern:

- Convert separate QA and calculation raw trees into `OmniMat_QA.tsv` and `OmniMat_CAL.tsv`.
- Resolve image references from raw JSON/JSONL against category-local image directories.
- Store both `image` base64 and `image_path` relative names when possible.
- Emit warnings for missing images instead of silently dropping references.
- Quote TSV fields because raw values can contain commas, tabs, JSON strings, and multi-line text.
- Keep rubric/scoring fields such as `key_points`, `scoring_weights`, `final_answer_format`, and `final_answer_list` as JSON strings.

Use this pattern when converting a local raw tree; do not assume the user's raw directory layout until inspecting it.

## Reference-only UI/browser pattern

Source evidence: `scripts/data_browser.py`.

The data browser launches Gradio and imports an API translator wrapper. Treat it as optional manual inspection only. For routine validation, prefer pandas column checks and `build_dataset(...).build_prompt(0)` rather than starting a service.

## TSV validation helper snippet

Use this pattern inside ad-hoc converters or review scripts:

```python
import json
import pandas as pd

REQUIRED = {'index', 'question'}

def parse_list_cell(value):
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    if text.startswith('['):
        return json.loads(text)
    return [text]

def validate_tsv(path):
    df = pd.read_csv(path, sep='\t')
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f'missing required columns: {sorted(missing)}')
    if not df['index'].is_unique:
        raise ValueError('index column is not unique')
    if 'image_path' in df:
        for row_id, value in zip(df['index'], df['image_path']):
            parse_list_cell(value)
    return df
```
