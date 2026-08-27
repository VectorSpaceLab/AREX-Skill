# CMCOQA Benchmark Format

CMCOQA is the Chinese Medical Complex Open-ended Question Answering benchmark used by this project to evaluate medical large language models on complex open-ended Chinese medical questions.

## Dataset construction facts

The benchmark documentation describes CMCOQA as follows:

- It starts from 100 manually written complex medical questions.
- GPT-4 plus Self-Instruct is used to expand the benchmark to a larger question set.
- Questions are categorized by ICD-10 disease classes, with some adjustments for coverage and balance.
- The checked `question.json` asset bundled with the project snapshot contains 200 question records.

## Question schema

The benchmark question asset is a single JSON array. Each object has:

| Field | Type | Meaning |
| --- | --- | --- |
| `question` | string | The Chinese open-ended medical question to ask the model. |
| `ICD-10` | string | The ICD-10 category label for the question. |

Representative shape:

```json
[
  {
    "question": "描述传染性的甲型肝炎的传播途径及预防措施。",
    "ICD-10": "Certain infectious and parasitic diseases"
  },
  {
    "question": "请说明腓骨神经病变的常见病因和治疗方法。",
    "ICD-10": "Diseases of the nervous system"
  }
]
```

The benchmark does **not** provide gold answers in this file. It is a question set plus category metadata. Do not validate it as supervised fine-tuning data and do not route it to training without first creating an appropriate answer-generation or evaluation dataset.

## Local category coverage observed in the checked asset

The checked question asset contains 19 ICD-10/category labels. The most frequent categories in the checked asset are:

| Count | Category |
| ---: | --- |
| 24 | Certain infectious and parasitic diseases |
| 18 | Diseases of the digestive system |
| 17 | Diseases of the skin and subcutaneous tissue |
| 16 | Diseases of the musculoskeletal system and connective tissue |
| 15 | Diseases of the circulatory system |
| 14 | Diseases of the nervous system |
| 13 | Diseases of the respiratory system |
| 13 | Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism |
| 13 | Endocrine, nutritional and metabolic diseases |
| 12 | Diseases of the eye and adnexa |
| 11 | Mental and behavioural disorders |
| 10 | Neoplasms |
| 10 | Diseases of the genitourinary system |

Lower-frequency labels include congenital abnormalities, pregnancy/childbirth, injury/poisoning, perinatal conditions, ear/mastoid disease, and `Others`.

## Evaluation dimensions

CMCOQA uses three dimensions, each scored from 0 to 3.

| Dimension | Sub-criteria | What to reward |
| --- | --- | --- |
| Completeness / 完整性 | Coverage / 覆盖度; Relevance / 相关性 | The answer covers all important parts of the question, such as etiology, diagnosis, treatment, prevention, or follow-up where relevant, and avoids unrelated information. |
| Depth / 深刻性 | Analytical depth / 分析深度; Insight / 见解 | The answer gives more than a surface description and includes useful medical reasoning or constructive suggestions. |
| Professionalism / 专业性 | Accuracy / 准确性; Conciseness / 简洁性; Terminology / 术语使用 | The answer is medically accurate, avoids misleading claims, is concise, and uses medical terminology appropriately. |

## Evaluation workflow guidance

- Generate an answer for each `question` field using the inference workflow, not this format sub-skill.
- Keep `ICD-10` with the generated answer so evaluators can stratify performance by disease class.
- Score model answers on the three dimensions above; the question file alone is insufficient for automatic correctness scoring.
- If creating a scored result file, add generated-answer and score fields in a new artifact rather than mutating the canonical question list.
