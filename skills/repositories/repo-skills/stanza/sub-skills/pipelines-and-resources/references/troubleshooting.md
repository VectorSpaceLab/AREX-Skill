# Troubleshooting

Use this page for the common pipeline and resource failures that are specific to Stanza's neural pipeline and local model cache.

## Missing resources or model files

**Symptom**: `LanguageNotDownloadedError` or a message about a missing model file.

**Why it happens**
- the target language directory is absent
- `resources.json` is missing from the active model dir
- `download_method=DownloadMethod.NONE` was used on a cache that is not fully populated

**Fix**
- run `stanza.download(...)` for the exact language/package combo
- or rerun with `--allow-download` in the smoke script
- or point `model_dir` at the cache that already contains the files

## Unsupported language or processor

**Symptom**: `UnsupportedProcessorError` or a `ValueError` saying the language is unsupported.

**Why it happens**
- the language code is not present in the active `resources.json`
- the requested processor/package combination is not defined for that language
- you asked for a custom setup without `allow_unknown_language=True`

**Fix**
- inspect installed models with `list_installed`
- choose a supported package from the resource maps
- for custom local models, use `allow_unknown_language=True` and explicit `*_model_path` kwargs

## Proxy or download failure

**Symptom**: `requests.exceptions.ConnectionError`, Hugging Face fetch failure, timeout, or a failed model download.

**Why it happens**
- the host requires a proxy
- the proxy was not passed through to the download call
- the network cannot reach the model host

**Fix**
- pass `proxies={"http": ..., "https": ...}` to `stanza.download(...)` or `Pipeline(...)`
- keep `--allow-download` off until the network path is proven
- pre-stage the resource files and use `DownloadMethod.NONE`

Note: Hugging Face URLs are handled through `huggingface_hub` when no proxy is set; with proxies, Stanza falls back to raw `requests`.

## PipelineRequirementsException

**Symptom**: pipeline construction fails with `PipelineRequirementsException` and a list of missing prerequisites.

**Why it happens**
- a processor needs upstream annotations that are not in the requested pipeline
- `pretagged` or `depparse_pretagged` was not set when it should have been
- the processor order does not satisfy the dependency graph

**Fix**
- add the prerequisite processors
- use `pretagged=True` only when the input already contains the expected tags
- if you already know the input is pretokenized, set `tokenize_pretokenized=True`

## CPU and GPU selection

**Symptom**: GPU was requested but the pipeline warns and stays on CPU, or device mismatches appear.

**Why it happens**
- CUDA is not visible to PyTorch
- `use_gpu=True` was set on a host without a working GPU
- a mixed device path was requested without an explicit device string

**Fix**
- inspect `torch.cuda.is_available()` and `torch.cuda.device_count()` first
- use `device='cpu'` for a guaranteed safe run
- use `device='cuda'` or `device='cuda:0'` only when the GPU is known to be available

## Pretokenized input

**Symptom**: the tokenizer splits text that was already tokenized, or the output looks wrong.

**Why it happens**
- `tokenize_pretokenized=True` was not set
- raw text was passed to a tokenizer configured for pretokenized input
- a list of already-tokenized documents was not wrapped the way the pipeline expects

**Fix**
- set `tokenize_pretokenized=True`
- pass tokenized text or prebuilt `Document` objects
- if you are processing a batch, use `process_many` or `bulk_process` rather than a manual loop

## Model cache staleness

**Symptom**: files exist but the pipeline still redownloads them, or the cache appears to mix old and new versions.

**Why it happens**
- the `.pt` file checksum does not match the resources metadata
- an older cache version is still present alongside the current one
- `resources.json` is stale relative to the model files

**Fix**
- inspect the cache with `list_installed`
- rerun with `DownloadMethod.DOWNLOAD_RESOURCES`
- remove the stale language/processor/package directory if needed, then redownload

## Quick recovery checklist

1. Check `resources.json` and `list_installed` output.
2. Decide whether you need an offline run or an explicit download.
3. Pick the exact language, package, and processor set.
4. Force CPU first if the failure looks device-related.
5. Only allow downloads when the user has explicitly approved them.

## Verification basis

These troubleshooting routes were distilled from Stanza 1.14.0 source, tests, demos, and installed-package inspection. Check the root provenance file before treating them as current for a different checkout or package version.
