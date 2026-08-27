# Benchmark-authoring troubleshooting

Use this table when dataset construction, prompt building, converter output, video preset setup, or evaluator logic fails before or during a VLMEvalKit run.

| Symptom | Likely cause | Probe | Fix |
| --- | --- | --- | --- |
| `build_dataset(name)` returns `None` | `LMUData/<name>.tsv` missing for an unsupported custom dataset | Check `LMUData` and list the expected TSV name | Put `<name>.tsv` under `LMUData`, add a `--data-config` entry, or register a dataset class. |
| Warning that TSV has no `question` column | Required custom fallback column missing or differently cased | `python -c "import pandas as pd; print(pd.read_csv('file.tsv', sep='\t').columns.tolist())"` | Add `question`; do not rely on `prompt` or `query` unless your subclass remaps it. |
| `index` collisions or strange circular MCQ behavior | Non-unique `index` or reused grouped ids without `g_index` semantics | `df['index'].is_unique` and `df[['index']].head()` | Make `index` unique; only use circular/grouped ids when the evaluator expects them. |
| Custom MCQ becomes text-only MCQ | TSV has `A`/`B` but no `image` or `image_path` | Inspect columns | Add `image_path` or `image`, or intentionally use `CustomTextMCQDataset`. |
| Custom open-ended image VQA is treated as MCQ type | Unknown dataset name defaults to `MCQ` unless name contains `openended` | `from vlmeval.dataset import DATASET_TYPE; print(DATASET_TYPE(name))` | Use a clearer dataset name, a `--data-config` class, or a registered subclass with `TYPE = 'VQA'`. |
| Image path assertion from `dump_image` | `image` missing and `image_path` cannot be found as absolute or under the dataset image root | Print `line['image_path']` and check files under `LMUData/images/<dataset-root>/` | Store correct relative paths, set the dataset-specific image root env var, or embed `image` base64. |
| Multi-image rows use one long string instead of a list | `image_path` list was not JSON-encoded | Try `json.loads(cell)` for rows starting with `[` | Write lists with `json.dumps(list, ensure_ascii=False)`. Avoid comma-joined paths. |
| Prompt has fewer/more images than expected | Number of `<image token>` / `<image>` markers does not match `image_path` list length | Print `question.count('<image')` and parsed image list length | Align markers and images; make `build_prompt` raise on mismatch before evaluation. |
| Base64 images fail to decode | `image` contains a data URI prefix, truncated text, or path instead of base64 | Check length and prefix of `image` cells | Strip data URI prefixes when needed or switch to `image_path`. |
| Large TSV keeps regenerating `_local.tsv` | File is larger than 1 GB and localization is forced or stale | Check `FORCE_LOCAL` and the presence of `<dataset>_local.tsv` | Unset `FORCE_LOCAL` after rebuilding; keep enough disk space for localized copies. |
| MD5 mismatch triggers re-download | `DATASET_MD5` does not match the local TSV | Check the class `DATASET_MD5` and local file hash | Update the TSV and MD5 together, or use a local override class/config during development. |
| Hugging Face download path fails | Optional dataset/converter download requires `huggingface_hub`, network, or token | Run the converter in local `--jsonl`/`--data-root` mode | Prefer local fixtures for validation; only run downloads when authorized. |
| ModelScope path expected but Hugging Face path used | `VLMEVALKIT_USE_MODELSCOPE` unset | Print the env var | Set `VLMEVALKIT_USE_MODELSCOPE=1` only when the target dataset class supports ModelScope and the package is installed. |
| LongDocURL images missing | TSV was built but page images were not prepared | Check `LONGDOCURL_IMAGE_ROOT` and a sample `image_path` | Prepare images separately or point `LONGDOCURL_IMAGE_ROOT` at existing `pdf_pngs`; TSV conversion alone is not enough. |
| MMLongBench images auto-download unexpectedly | `MMLB_AUTO_DOWNLOAD_IMAGES` default allows image preparation | Inspect env and class init behavior | Set `MMLB_AUTO_DOWNLOAD_IMAGES=0` for dry checks, then prepare images manually under the expected root. |
| MemLens images auto-download unexpectedly | `MEMLENS_AUTO_DOWNLOAD_IMAGES` default allows image preparation | Inspect env and class init behavior | Set `MEMLENS_AUTO_DOWNLOAD_IMAGES=0` for dry checks, then prepare images manually under `MEMLENS_IMAGE_ROOT`. |
| Video dataset raises `fps and nframe should not be set at the same time` | Preset or data config passed both positive values | Inspect the `supported_video_datasets` partial or config JSON | Choose either `nframe` or `fps`; make separate presets for frame-count and rate-based variants. |
| Video dataset disables frame splitting | Both `nframe <= 0` and `fps <= 0` | Print the dataset object fields after construction | Set one sampling mode, or accept direct-video input if the target model supports `dict(type='video')`. |
| `decord` import error appears | Video frame extraction dependency missing | Constructing `VideoBaseDataset` logs the missing package | Install video dependencies only when frame extraction is required; direct-video prompt classes may still need their own deps. |
| Video preset name not found | Preset not added to `supported_video_datasets` group map | `from vlmeval.dataset.video_dataset_config import supported_video_datasets; print(name in supported_video_datasets)` | Add a `partial(...)` entry and ensure its group is included in `dataset_groups`. |
| `build_prompt` returns strings or tuples | Prompt does not follow multimodal message format | Print `ds.build_prompt(0)` | Return a list of dicts with `type` and `value`, using `image`, `text`, or `video`. |
| Evaluator returns an unsupported type | `evaluate` returned a scalar/list/object | Inspect return type | Return a `dict` or `pandas.DataFrame`; dump detailed intermediates separately. |
| MCQ exact matching marks many failures | Predictions do not contain recognizable option labels or option text | Inspect `prediction`, option columns, and `log` in result file | Use clearer prompt wording, add deterministic post-processing, or use an authorized LLM judge. |
| LLM judge silently falls back to exact matching | `build_judge(...).working()` failed | Look for warnings and judge failure logs | Fix judge environment/credentials in the evaluation workflow; do not claim live judge verification from authoring checks. |
| `report_acc` omits category columns | TSV lacks `category` or `l2-category` | Inspect scored DataFrame columns | Add grouping columns before evaluation if the benchmark report requires them. |
| Test split lacks `answer` | Official benchmark may require server submission or no local score | Inspect `answer` column and dataset docs | Implement `evaluate` to skip local scoring or emit submission files; route running/submission details to evaluation. |
| Converter output has malformed JSON cells | Used Python `repr` or CSV quoting incorrectly | Run `json.loads` on structured cells | Use `json.dumps(..., ensure_ascii=False)` and write TSV with a real CSV/pandas writer. |
| Archive extraction is unsafe | Converter extracts tar members without path checks | Review extraction function | Use the safe extraction pattern in `converter-patterns.md`; never extract untrusted archives with raw `extractall`. |
| Gradio/data browser workflow blocks | Browser script launches a service and may import API wrappers | Check whether the task only needs schema inspection | Use pandas and `build_prompt` probes by default; launch UI only after explicit user authorization. |

## Minimal pre-handoff checklist

- TSV has `index` and `question`; `index` is unique.
- Image datasets have either `image` or valid `image_path` for representative rows.
- Multi-image cells parse as JSON lists and align with prompt image tokens.
- MCQ datasets have `A` and `B` at minimum, plus `answer` for local scoring.
- Video presets set exactly one of `nframe` or `fps`.
- `build_dataset(name)` returns the intended class or expected custom fallback.
- `ds.build_prompt(0)` returns only dictionaries with `type` and `value`.
- `evaluate` returns `dict` or `pandas.DataFrame` and writes optional detail files without mutating source data.
- Full model inference, live judges, downloads, and Gradio services are either explicitly authorized or deferred.
