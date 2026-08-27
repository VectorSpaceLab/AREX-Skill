# Legacy Extension Troubleshooting

## Model files

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `CWSModel.load` fails | Path does not point to a legacy CWS model binary. | Check the file exists and belongs to the expected task. Use the trainer checker for path diagnostics. |
| `LTP("LTP/legacy")` fails after config load | The legacy model directory/cache is incomplete. | Provide a complete legacy model directory with config and task model files. |
| POS or NER direct model predicts with shape errors | Inputs are not word lists or POS tags do not align with words. | Ensure `len(words) == len(pos_tags)` before calling NER. |

## Task dependencies

- Legacy NER depends on POS. With the high-level wrapper, ask for `['cws', 'pos', 'ner']` together.
- With direct classes, call CWS first, POS second, and NER third.
- If a task already has tokenized words, you may skip CWS for POS, but NER still needs POS.

## Character-rule mistakes

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Segmentation over-merges product strings | A concat rule is too broad. | Use directed rules first (`enable_type_concat`) before bidirectional rules (`enable_type_concat_d`). Validate on examples. |
| Segmentation over-splits mixed scripts | A cut rule is too broad. | Disable the type rule or narrow it to one direction. |
| `CharacterType` attribute missing | Wrong enum name/case. | Use exactly `Digit`, `Roman`, `Hiragana`, `Katakana`, `Kanji`, or `Other`. |

## Trainer setup

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Trainer complains about missing train/eval data | Path is wrong or data was not staged. | Run `legacy_trainer_config_check.py` before training. |
| POS/NER trainer fails at construction | Labels were omitted. | Pass labels for POS/NER tasks. |
| Unknown algorithm | Algorithm name not one of the implemented values. | Use `AP`, `Pa`, `PaI`, or `PaII`; pass a margin/param for `PaI`/`PaII` when needed. |
| Training is slow | Epochs, data size, or algorithm/parallelism choices are expensive. | Ask before long training; start with a tiny fixture and low epoch count. |

## Parallelism

Parallel prediction is useful for batches but can add overhead for tiny examples. Keep `parallelism=True` for real batches; set it explicitly in tests when reproducibility or easier debugging matters.
