# Dataset Reference

This repository skill treats Chinese-BERT-wwm as a model/data resource repository. Some dataset folders contain only a source pointer because the data is external or copyright-restricted; do not assume every benchmark dataset is bundled.

## Dataset and task map

| Dataset | Task family | Language/script notes | Repository availability | Source pointer / constraint | Expected metric family |
| --- | --- | --- | --- | --- | --- |
| CMRC 2018 | Extractive reading comprehension, SQuAD-style span extraction | Simplified Chinese | Source pointer only | `https://github.com/ymcui/cmrc2018` | EM / F1 |
| DRCD | Extractive reading comprehension, SQuAD-style span extraction | Traditional Chinese | Source pointer only | `https://github.com/DRCKnowledgeTeam/DRCD` | EM / F1 |
| CJRC | Legal/judiciary reading comprehension | Simplified Chinese, legal domain | Source pointer only; benchmark test caveat | `http://cail.cipsc.org.cn`; repository note says the test set used in experiments is in-house and cannot be provided | EM / F1 |
| XNLI | Natural language inference | Chinese portion of multilingual XNLI; labels are entailment, neutral, contradiction/contradictory depending on source naming | Source pointer only | Original: `https://github.com/facebookresearch/XNLI`; BERT fine-tuning source used by repo: `https://github.com/google-research/bert/blob/master/multilingual.md#fine-tuning-example` | Accuracy |
| ChnSentiCorp | Binary sentiment analysis | Chinese reviews; bundled examples include simplified and traditional text | Included fixture archive | `https://github.com/pengming617/bert_classification/tree/master/data`; archive schema below | Accuracy |
| LCQMC | Sentence-pair semantic matching | Simplified Chinese sentence pairs | Source pointer only; copyright-restricted direct download | `http://icrc.hitsz.edu.cn/info/1037/1146.htm`; README note says copyright restrictions prevent a direct download link and users may search GitHub or contact source owners | Accuracy |
| BQ Corpus | Sentence-pair semantic matching, banking domain | Simplified Chinese sentence pairs | Source pointer only; copyright-restricted direct download | `http://icrc.hitsz.edu.cn/info/1037/1162.htm`; README note says copyright restrictions prevent a direct download link and users may search GitHub or contact source owners | Accuracy |
| THUCNews | Document-level text classification | Chinese news; repository uses a 10-class subset in baselines | Source pointer only; large external data | `https://github.com/gaussic/text-classification-cnn-rnn`; README note says file is too large and should be downloaded from original source | Accuracy |
| MSRA NER | Named entity recognition | Chinese NER corpus | Source pointer only | `https://github.com/OYE93/Chinese-NLP-Corpus` | NER metrics are not part of the main benchmark tables in this repository |
| PeopleDaily | Character-level BIO named entity recognition | Chinese character rows with `PER`, `ORG`, `LOC` tags | Included fixture archive | `https://github.com/ProHiryu/bert-chinese-ner/tree/master/data`; archive schema below | NER metrics are not part of the main benchmark tables in this repository |
| Weibo | Binary sentiment analysis | Informal Weibo/microblog text | Included fixture archive | `https://github.com/SophonPlus/ChineseNlpCorpus/blob/master/datasets/weibo_senti_100k/intro.ipynb`; archive schema below | Accuracy when used as sentiment classification |

## Included archive schemas

Use `scripts/validate_dataset_schema.py` for executable validation. The details below are the expected schemas distilled from bundled archives.

### ChnSentiCorp archive

- Supported task id for validator: `chnsenticorp`.
- Archive members: `train.tsv`, `dev.tsv`, `test.tsv`.
- Encoding observed in the bundled archive: UTF-8 with optional BOM (`utf-8-sig` works).
- Delimiter: tab.
- Header: exactly `label<TAB>text_a`.
- Rows: `label` must be `0` or `1`; `text_a` must be non-empty review text.
- Sample rows in the repository include both simplified and traditional Chinese text. Do not normalize script unless the user's downstream pipeline explicitly requires it.
- Observed split sizes from the bundled archive by line-level parsing: train 9,600 examples, dev 1,200 examples, test 1,200 examples.

### Weibo archive

- Supported task id for validator: `weibo`.
- Archive members: `train.csv`, `dev.csv`, `test.csv`.
- Encoding observed in the bundled archive: UTF-8 with optional BOM (`utf-8-sig` works).
- Delimiter: comma, with standard CSV parsing.
- Header: exactly `label,review`.
- Rows: `label` must be `0` or `1`; `review` must be non-empty microblog text. The review field may contain punctuation, URLs, hashtags, mentions, emoji-like bracket tokens, and commas; parse with CSV rather than naive string splitting.
- Observed split sizes from the bundled archive: train 99,988 examples, dev 10,000 examples, test 10,000 examples.

### PeopleDaily archive

- Supported task id for validator: `peopledaily`.
- Archive members: `train.txt`, `dev.txt`.
- Encoding observed in the bundled archive: UTF-8 with optional BOM (`utf-8-sig` works).
- Format: plain text with one character and one tag per non-empty line, separated by whitespace. Blank lines separate sentences.
- Row schema: `char TAG`, where `char` is exactly one Unicode character and `TAG` is one of `O`, `B-PER`, `I-PER`, `B-ORG`, `I-ORG`, `B-LOC`, `I-LOC`.
- The bundled data contains BIO-style tags but may include standalone `I-*` rows after blank boundaries; the validator checks tag vocabulary and row shape, not strict BIO transition legality.
- Observed non-empty row counts from the bundled archive: train 2,169,879 rows plus 50,658 blank separators; dev 172,601 rows plus 4,631 blank separators.

## Availability rules

- Source-pointer-only datasets remain the user's responsibility to acquire under the dataset owner's terms.
- Copyright-restricted datasets such as LCQMC and BQ Corpus must not be downloaded by a bundled script. Provide the public source pointer and tell the user to search or contact the original owner when the README says so.
- Large external datasets such as THUCNews should be obtained from the original source, not from this skill.
- CJRC benchmark numbers in this repository have an in-house test caveat; do not present them as official final CJRC leaderboard values.
- The included fixture archives are useful for schema checks and examples. They do not prove a user's independently downloaded dataset is complete or license-compatible.
