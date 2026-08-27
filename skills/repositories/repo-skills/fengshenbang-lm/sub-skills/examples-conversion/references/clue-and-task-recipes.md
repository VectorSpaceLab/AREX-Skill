# CLUE and task recipe planning

This reference covers the high-level CLUE/classification example family. It does not replace `../pipelines-cli/SKILL.md` for CLI mechanics or `../data-training/SKILL.md` for dataloaders/Trainer/checkpoint flags.

## CLUE recipe overview

The CLUE1.1 example family separates tasks into two routes:

| CLUE task | Task type | Example route | Notes |
|---|---|---|---|
| AFQMC | Semantic matching | UniMC | Sentence pair classification: `sentence1`, `sentence2`, label `0/1`. |
| TNEWS | News classification | UniMC | Single sentence with label descriptions. |
| IFLYTEK | App description classification | UniMC | Many label categories; label description mapping matters. |
| WSC | Winograd/coreference judgment | UniMC | Text plus target span/pronoun, converted to yes/no choice wording. |
| OCNLI | Natural language inference | UniMC | Sentence pair with contradiction/neutral/entailment labels. |
| CSL | Keyword/abstract judgment | UniMC | Abstract plus keywords converted into choice text. |
| CHID | Idiom cloze | UniMC | Candidate idioms; prediction aggregation is non-trivial. |
| C3 | Multiple-choice reading comprehension | UniMC | Dialogue/passage plus question and choices. |
| CMRC2018 | Extractive reading comprehension | Ubert | Uses span/extractive QA route rather than UniMC classification route. |

The examples convert downloaded official CLUE data into a unified JSONL format, train UniMC/Ubert models, then convert predictions into CLUE submission formats. Keep benchmark download/submission as user-managed external steps.

## Unified classification-style data shape

Most UniMC-converted tasks produce JSONL records resembling:

```json
{
  "task_type": "语义匹配",
  "texta": "sentence or passage",
  "textb": "optional second sentence",
  "question": "optional question",
  "choice": ["不相似", "相似"],
  "answer": "相似",
  "label": 1,
  "id": 0
}
```

Task-specific fields may vary, but `choice`, `label`, and `id` are important for training and submission conversion. When adapting a new dataset, preserve a stable ID and deterministic choice order.

## CMRC2018 / Ubert data shape

CMRC2018 is extractive reading comprehension. The converted records contain context/question/answer span information rather than simple class labels. Treat it as a Ubert/extractive QA route and do not force it into the generic UniMC classification pattern.

## Planning steps for CLUE-style work

1. Confirm whether the user wants **leaderboard reproduction**, **data conversion**, **training command planning**, or **prediction-to-submission conversion**.
2. Confirm the user already has official benchmark data. Do not download it from this skill.
3. Decide route:
   - UniMC for the eight classification/multiple-choice tasks.
   - Ubert for CMRC2018 extractive QA.
4. For conversion, map original task fields into the unified JSONL schema and preserve `id` values.
5. For training, use user-provided model ID/path, output root, GPU count, and max length; route Trainer details to `../data-training/SKILL.md`.
6. For submission conversion, verify prediction JSONL contains `id`, `choice` when needed, and numeric `label` or task-specific span output.

## Classification examples outside CLUE

The classification example family also demonstrates generic downstream classification fine-tuning, including:

- DDP fine-tuning with a Roberta-style model.
- Deepspeed fine-tuning for speed/memory.
- Offload-style fine-tuning of a larger Erlangshen model with lower VRAM.
- AFQMC as the default illustrative dataset.

For generic classification, prefer `../pipelines-cli/SKILL.md` because it owns `fengshen-pipeline text_classification train|predict` mechanics and fixture creation. This file is only for high-level model-family recipe planning.

## Useful task-label mappings

| Task | Original labels | Unified choice idea |
|---|---|---|
| AFQMC | `0`, `1` | `不相似`, `相似` |
| OCNLI | `contradiction`, `neutral`, `entailment` | `矛盾`, `自然`, `蕴含` |
| WSC | `true`, `false` | `是`, `不是` with target span/pronoun inserted into text |
| CSL | `0`, `1` | Whether provided keywords can summarize the abstract |
| TNEWS/IFLYTEK | label descriptions | Use human-readable label descriptions as choices; keep submission label IDs separately. |
| CHID | idiom candidates | Candidate order determines label index; aggregation is needed because one passage can contain multiple blanks. |
| C3 | multiple-choice options | `choice` from each question; label is answer index when available. |

## Prediction-to-submission considerations

- Do not assume a uniform output format across tasks.
- TNEWS/IFLYTEK convert a predicted choice description back to official numeric label IDs.
- OCNLI maps indices back to string labels.
- AFQMC maps indices back to `0`/`1`.
- CHID and CSL perform aggregation/post-processing beyond simple line-wise mapping.
- CMRC2018 writes an answer dictionary keyed by question ID.

If the user asks to implement these converters, create a new safe script with explicit input/output paths and tests; do not run conversion against benchmark data without approval because it writes output files.

## Resource and dependency gates

| Step | Backend | Dependencies | Side effects |
|---|---|---|---|
| Static schema planning | Any | None beyond Python/JSON knowledge | None. |
| Preprocessing downloaded CLUE data | CPU | Python, JSON, sometimes text keyword extraction packages | Writes converted JSONL. |
| UniMC/Ubert training | CUDA recommended | Fengshen package, Transformers, Lightning, Torch, optional Deepspeed | Writes checkpoints/logs/predictions. |
| Prediction-to-submission conversion | CPU | Python/JSON, task-specific converter logic | Writes submission files. |

## Safe checklist command

```bash
python ../scripts/check_recipe_requirements.py --recipe clue --device cuda --gpus 1 --vram-gb 16
python ../scripts/check_recipe_requirements.py --recipe classification --device cpu
```

## Troubleshooting

| Symptom | Likely cause | Safe response |
|---|---|---|
| Prediction labels are shifted | `choice` order differs between preprocessing and submission conversion | Preserve choice ordering and store task-specific label maps with artifacts. |
| IDs do not match official submission | Data came from a mirrored or transformed dataset with changed IDs | Use official data for final submission; keep original IDs through conversion. |
| CMRC2018 treated as classification | Wrong route | Use Ubert/extractive QA schema, not UniMC classification schema. |
| CHID/CSL submission scores look wrong | Required aggregation logic not applied | Recreate post-processing with task tests before final output. |
| Training script cannot find files | Source shell scripts assumed local relative directories | Build paths from user-provided data/output roots; do not copy source paths. |
| Model download blocked | Model ID requires network | Ask for local model cache/path or network approval. |
