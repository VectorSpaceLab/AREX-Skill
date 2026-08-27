# Training and Dataset Troubleshooting

Use this reference when a Flair training or corpus-loading task fails under the public pip-installed package. CPU local-file workflows are the verified baseline. Keep downloads, CUDA, ONNX/provider runtimes, SciSpaCy, `pyab3p`, and multi-GPU marked optional unless separately proven.

## Import and environment failures

**Symptom: `ModuleNotFoundError: No module named 'flair'`.**

- Install the public package in the active Python environment.
- Re-run `python -c "import flair; print(flair.__version__)"` before training.
- Do not depend on project-local package files being importable.

**Symptom: device unexpectedly uses CUDA or CPU.**

- Set `FLAIR_DEVICE=cpu` before importing `flair` for CPU baseline behavior.
- In scripts, set `flair.device = torch.device("cpu")` after import when needed.
- Verify the device line in trainer logs and any `torch.cuda.is_available()` checks.

## Unexpected downloads or cache writes

**Symptom: prepared dataset or model construction tries to download.**

- Use local corpus readers: `ColumnCorpus`, `MultiFileColumnCorpus`, JSONL readers, `ClassificationCorpus`, `CSVClassificationCorpus`, or `UniversalDependenciesCorpus`.
- Use local model paths or pre-approved cached resources.
- Set `FLAIR_CACHE_ROOT` before importing `flair` when downloads are allowed and should be isolated.
- In the bundled CLI, pass `--allow-downloads` only when public dataset/model downloads are acceptable.

## ColumnCorpus issues

**Symptom: all labels are `O` or the dictionary is empty.**

- Check `column_format`; the text column must map to `"text"` and the target annotation column must match the `label_type` passed to `make_label_dictionary(...)`.
- Confirm whether the label column uses BIO/BIOES span tags or token-level tags.
- If a header row is present, use a reader path that supports `skip_first_line=True` or remove the header.
- If the file is tab-separated, pass `column_delimiter="\t"`.

**Symptom: sentence count is wrong.**

- Ensure blank lines separate sentences.
- Check whether comment lines start with the configured `comment_symbol`.
- If boundary markers such as `-DOCSTART-` appear as sentences, use `banned_sentences` or `document_separator_token` intentionally.
- Disable auto split discovery and pass explicit file names when multiple candidate files are present.

**Symptom: offsets or span labels drift after tokenization.**

- Avoid retokenizing loaded column data unless necessary.
- If using `use_tokenizer`, inspect `sentence.to_tokenized_string()` and `sentence.get_spans(label_type)` for several examples.
- Use a `space-after` column when exact original whitespace matters.

## JSONL issues

**Symptom: `ImportError` for `JsonlCorpus` or `MultiFileJsonlCorpus`.**

- First try `from flair.datasets import JsonlCorpus, MultiFileJsonlCorpus`.
- If that fails, use `from flair.datasets.sequence_labeling import JsonlCorpus, MultiFileJsonlCorpus`.

**Symptom: char-span JSONL fails to load.**

- Ensure each JSON line has the configured text column and label column.
- Labels must be lists like `[start_char, end_char, label]`.
- Confirm offsets use Python slice semantics: start inclusive, end exclusive.
- Remove malformed or whitespace-only spans.
- Use a deliberate tokenizer and inspect loaded examples before training.

## Classification corpus issues

**Symptom: many classification examples are skipped.**

- `ClassificationCorpus` expects FastText labels at the beginning of each line, such as `__label__sports text`.
- Set `allow_examples_without_labels=True` only if unlabeled examples are intentional.
- Check `skip_labels`, `label_name_map`, `filter_if_longer_than`, and truncation settings.

**Symptom: CSV labels are missing.**

- In `CSVClassificationCorpus`, label column names must start with `"label"`.
- Text columns must map to `"text"`; paired text columns map to `"pair"`.
- If there is a header row, set `skip_header=True`.
- Pass the correct CSV dialect parameters, especially `delimiter` for TSV.

## CoNLL-U issues

**Symptom: wrong label type for UD training.**

- Use `"upos"` for universal POS, `"pos"` for language-specific POS, `"lemma"` for lemmas, `"dependency"` for dependency relation labels, and morphology-specific feature labels for morphological attributes.
- Call `make_label_dictionary(...)` with the intended label type and inspect dictionary items.

**Symptom: multiword token behavior changes counts.**

- `split_multiwords=True` splits UD multiword tokens into component words.
- `split_multiwords=False` keeps the multiword surface token and skips component rows.
- Keep the setting consistent between experiments and reports.

## Label dictionary issues

**Symptom: `<unk>` appears in a closed NER/POS dictionary.**

- Pass `add_unk=False` for closed sequence labels when unknown predictions are not desired.
- Keep `add_unk=True` for open-ended labels, span classification, or entity linking only when appropriate.

**Symptom: dev/test labels are missing from evaluation dictionary.**

- Use `add_dev_test=True` only if the evaluation contract permits building from dev/test labels.
- Otherwise fix training data coverage or document unseen-label limitations.

## Trainer and output issues

**Symptom: no model file appears.**

- Check `save_final_model`; if `False`, `final-model.pt` is intentionally skipped.
- If relying on best-model selection, ensure a dev split exists and the evaluation policy saves a best model.
- Inspect `training.log` and exceptions before assuming success.

**Symptom: old best models disappear.**

- Flair can delete previous `best-model*` files in the output folder at the start of a fresh epoch-zero run.
- Use a new output directory per run, or intentionally continue from saved weights in a controlled directory.

**Symptom: exact resume is unclear.**

- Save optimizer state if exact resume is required.
- Verify the active installed Flair API for checkpoint-loading helpers before claiming bit-exact resume.
- If only weights are loaded, describe the run as continued fine-tuning from saved model weights.

## Memory and speed issues

**Symptom: host RAM grows during training.**

- Use `embeddings_storage_mode="none"`.
- Downsample for smoke checks with a fixed seed.
- Use dataset memory modes such as `"partial"` or `"disk"` for text classification.
- Reduce `mini_batch_size` and use `mini_batch_chunk_size`.

**Symptom: CUDA out of memory.**

- CUDA is optional/unverified unless proven; first reproduce on CPU or a tiny sample when possible.
- Use `embeddings_storage_mode="none"`.
- Lower `mini_batch_chunk_size`, then lower `mini_batch_size`.
- Avoid `embeddings_storage_mode="gpu"` unless memory headroom is measured.
- Consider shorter documents, less context, or a smaller transformer with the embeddings sub-skill.

## Relation and span model issues

**Symptom: relation model trains but predicts no relations.**

- Confirm entity spans exist in the layer named by `entity_label_type` or `entity_label_types`.
- Confirm relation labels exist in `label_type`.
- Inspect negative-pair generation, `entity_pair_filters`, `entity_pair_labels`, thresholds, and `train_on_gold_pairs_only`.
- For `RelationClassifier`, check context length and marker encoding choices.

**Symptom: `SpanClassifier` cannot find spans.**

- Verify `span_label_type` matches the existing span layer in the corpus.
- Verify the target label type is the span-classification label, such as `"nel"`, not the NER span layer.
- Candidate generators can require external dictionaries or downloads; mark them optional unless proven.

## TARS issues

**Symptom: TARS model construction downloads resources.**

- TARS constructors and `load(...)` can use transformer model names or pretrained TARS IDs.
- Use local/cached paths or explicit download approval.
- Dry-run corpus and label handling before constructing TARS.

**Symptom: labels are wrong after adding or switching tasks.**

- Keep `task_name`, `label_dictionary`, and `label_type` together in the handoff record.
- For zero-shot prediction, candidate labels are provided at prediction time; route inference-only use to `tagging-and-annotations`.

## Multi-GPU issues

**Symptom: `multi_gpu=True` fails because distributed state is missing.**

- Wrap the main function in `flair.distributed_utils.launch_distributed(main, ...)`.
- Pass `multi_gpu=True` to `trainer.train(...)` or `trainer.fine_tune(...)` inside that launched function.
- Verify CUDA and at least two GPUs first; CPU baseline does not prove this path.

**Symptom: distributed run hangs or worker corpora differ.**

- Seed before corpus construction and downsampling.
- Use explicit split files.
- Avoid worker-local downloads or random preprocessing.
- Start with a tiny corpus and one epoch.
