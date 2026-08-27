# Workflows

## Purpose

Use this when you need the command-level data and evaluation workflows behind scispaCy's training and packaging setup.

## 1) Count token and document frequencies

Use the bundled helper on a directory of raw text files:

```bash
python scripts/count_word_frequencies.py --raw-dir /path/to/raw --output-path /tmp/freqs.tsv
```

What it does:

- tokenizes each file with the scispaCy rule-based tokenizer,
- counts token and document frequency,
- and writes a tab-separated frequency file.

Use this before vocabulary conversion when you need a corpus-specific token frequency summary.

## 2) Convert frequency counts to spaCy vocab JSONL

```bash
python scripts/convert_freqs.py --input_path /tmp/freqs.tsv --output_path /tmp/vocab.jsonl --min_word_frequency 1000
```

This turns the frequency file into the JSONL vocabulary format used by the project configs.

## 3) Evaluate a model on a TSV or MedMentions split

```bash
python scripts/evaluate_ner.py \
  --model_path /path/to/model \
  --dataset /path/to/ner.tsv \
  --output_path /tmp/metrics.json
```

For MedMentions:

```bash
python scripts/evaluate_ner.py \
  --model_path /path/to/model \
  --dataset medmentions-test \
  --med_mentions_folder_path /path/to/medmentions
```

Use `--gpu_id` only if the chosen model and host actually support a GPU-backed evaluation.

## 4) Export UMLS to JSONL

```bash
python scripts/export_umls_json.py --meta_path /path/to/UMLS/META --output_path /tmp/umls.jsonl
```

This reads the UMLS concept, type, and definition files and writes a JSONL KB suitable for `KnowledgeBase`.

## 5) Summarize packaged model metrics

```bash
python scripts/print_out_metrics.py --base-path /path/to/packages
```

Use this when you already have the package-generated JSON metric files and want a concise summary.

## 6) Understand the project registry

The project defines these workflow families:

- `small`
- `medium`
- `large`
- `scibert`
- `specialized-ner`
- `all`

The bundled API reference records the reader and callback names that those workflows use. The registry names matter because the config-driven training/evaluation paths refer to them directly; use this sub-skill's references rather than reopening the original checkout for routine work.

## 7) Smoke the workflow stack

The root `scripts/smoke_scispacy.py` helper covers the installed package and the core component/linker stack, but not the data-prep commands above. Use a tiny fixture-backed run for each workflow when you need stronger assurance.

## When to stop and check troubleshooting

Read the troubleshooting reference if you see:

- missing or malformed MedMentions/BIO input,
- an empty frequency output,
- stale helper names such as `combined_rule_sentence_segmenter`,
- large download or cache failures,
- or a GPU flag on a host that is only meant for CPU evaluation.
