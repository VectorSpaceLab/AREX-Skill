---
pretty_name: "Replace with dataset display name"
language:
- en
license: "replace-with-license-id"
task_categories:
- text-classification
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: train
    path: "data/train.*"
  - split: validation
    path: "data/validation.*"
  default: true
---

# Dataset Card for Replace with Dataset Name

## Dataset Summary

Describe what the dataset contains, who created it, why it was created, and the intended use cases. Replace placeholders before publishing.

## Dataset Structure

- **Configurations:** `default`
- **Splits:** `train`, `validation`
- **File format:** Replace with CSV, JSONL, Parquet, Arrow, image/audio folder, or another supported format.
- **Columns:** List each column and its meaning. Route detailed `Features` design to the features/formats guidance.

## Data Sources and Collection

Describe original sources, collection dates, filtering, annotation process, and any transformations applied before upload.

## Intended Uses and Limitations

State recommended uses, out-of-scope uses, known limitations, and any quality caveats.

## Bias, Privacy, and Safety

Describe known biases, sensitive content, PII handling, consent, anonymization, and recommended safeguards.

## Licensing and Citation

Provide license details and citation instructions. Do not publish without verifying that redistribution is allowed.

## Contact

Provide a maintainer, organization, or issue/discussion location for questions and dataset corrections.
