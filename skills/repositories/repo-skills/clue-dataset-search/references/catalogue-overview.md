# Catalogue Overview

## Purpose

Read this when you need to understand the CLUEDatasetSearch catalogue shape,
choose task-family routes, or search the bundled JSON index without reopening
the source repository.

## Repository shape captured by this skill

The catalogue is a set of Markdown tables. Each category table uses these
fields, although many rows leave some cells blank:

| Field | Meaning for future agents |
|---|---|
| `ID` | Row number inside the category table. It is not a global dataset id. |
| `标题` / title | Dataset or resource name, usually linked to an external page. |
| `数据集更新日期` / updated | Date as written by the catalogue; formats are inconsistent. |
| `数据集提供者` / provider | Person, institution, company, organizer, or repository named as provider. |
| `许可` / license | License text if the catalogue provided it; blank does not mean unrestricted. |
| `说明` / description | Short Chinese description with scale, domain, task, or format hints. |
| `关键字` / keywords | Task/domain hints; spelling and punctuation are inconsistent. |
| `类别` / task type | Source table's task/category label. |
| `论文地址` / paper | Paper or benchmark page when available. |
| `备注` / note | Language, extra website, password, fee, or other notes. |

## Bundled index

The file [dataset-index.json](dataset-index.json) contains a distilled index
from the category-specific Markdown tables. It intentionally stores catalogue
metadata only; it does not include dataset contents.

Index summary:

| Category slug | Source category name | Entries | Owning sub-skill |
|---|---:|---:|---|
| `ner` | NER | 9 | `sequence-labeling` |
| `qa` | QA | 9 | `qa-reading` |
| `sentiment-analysis` | 情感分析 | 11 | `classification-sentiment` |
| `text-classification` | 文本分类 | 19 | `classification-sentiment` |
| `text-matching` | 文本匹配 | 17 | `matching-nli` |
| `summarization` | 文本摘要 | 24 | `generation-corpora` |
| `machine-translation` | 机器翻译 | 16 | `generation-corpora` |
| `knowledge-graph` | 知识图谱 | 1 | `generation-corpora` |
| `corpus` | 语料库 | 14 | `generation-corpora` |
| `reading-comprehension` | 阅读理解 | 31 | `qa-reading` |

The bundled index has 151 category-row entries. The original root catalogue
contains a duplicated `AmazonQA` row; the bundled index uses the category files
as the canonical row source to avoid carrying that root-table duplicate.

## Search strategy

Use the helper first when the user gives a title, acronym, domain, language, or
category hint:

```bash
python scripts/search_dataset_index.py --query cluener
python scripts/search_dataset_index.py --query medical --language Chinese
python scripts/search_dataset_index.py --category 阅读理解 --query legal --limit 0
python scripts/search_dataset_index.py --category text-matching --query finance --json
```

Search is case-insensitive and ANDs repeated `--query` terms. The helper scans
title, category, task type, keywords, description, provider, license, note, URL,
paper URL, and inferred language signals.

## How to compare candidates

1. Prefer the sub-skill that owns the task semantics, not merely the first title
   match. For example, `cMedQA` appears relevant to QA and matching; choose
   `qa-reading` for answer selection/QA and `matching-nli` for question-answer
   relevance or pair matching.
2. Compare language and domain signals from the description and note fields.
3. Treat dataset scale numbers as catalogue claims; verify from the external
   provider before reporting exact training-set sizes in a paper or benchmark.
4. Treat blank license cells as unknown. Do not infer open use from a public
   link.
5. When the access URL is a competition site, LDC catalogue, Baidu Pan share,
   or researcher's personal page, warn that accounts, passwords, fees, or
   contact requests may be required.

## Duplicate and overlap handling

- Dataset names can appear in multiple categories when one dataset supports
  more than one task. Keep the category slug in citations and recommendations.
- Some rows describe broad corpora that can become classification, QA, or
  pretraining data after additional labeling; route by the user's intended use.
- Some English datasets appear in Chinese task-family tables for comparison or
  benchmark context. Do not assume every row is Chinese.
- Some rows use outdated or malformed Markdown links. Use the bundled URL as a
  clue, then verify externally if the next task depends on it.
