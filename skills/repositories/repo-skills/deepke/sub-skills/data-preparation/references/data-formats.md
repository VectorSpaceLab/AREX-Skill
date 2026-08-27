# DeepKE data formats for preparation

Use this reference to shape input files before running the bundled data-preparation scripts. The schemas below are distilled into this sub-skill so future use does not depend on the original repository checkout.

## Shared conventions

- Use UTF-8 text unless a tool explicitly requires another encoding.
- Keep train/dev/test splits separate after preparation.
- Label names must match the downstream DeepKE configuration or label vocabulary exactly, including case and punctuation.
- Offsets are Python-style character offsets: `start_offset` is inclusive and `end_offset` is exclusive.
- For small smoke files, inspect the converted output manually before launching training.

## NER supervised text (`txt`)

DeepKE standard NER uses a CoNLL-like BIO text file:

```text
秦 B-PER
始 I-PER
皇 I-PER
兵 O
马 O
俑 O

北 B-LOC
京 I-LOC
```

Rules:

- One token or character plus one label per line.
- Blank lines separate sentences/documents.
- Entity starts use `B-LABEL`; continuation positions use `I-LABEL`; outside positions use `O`.
- The classic Chinese examples are character-level. English or whitespace-delimited data may be token-level if the downstream loader/config expects token-level input.

## NER supervised JSON

The bundled converter accepts two common NER JSON shapes.

DeepKE-style list:

```json
[
  {
    "sentence": "秦始皇兵马俑位于陕西省西安市。",
    "entities": [
      {"word": "秦始皇", "label": "PER"},
      {"word": "陕西省", "label": "LOC"}
    ]
  }
]
```

Doccano-style JSON/JSONL with `entities` objects:

```json
{
  "id": 10,
  "text": "University of California is located in California.",
  "entities": [
    {"id": 15, "label": "ORG", "start_offset": 0, "end_offset": 24},
    {"id": 16, "label": "LOC", "start_offset": 39, "end_offset": 49}
  ],
  "relations": []
}
```

Doccano sequence-labeling exports that use `label` or `labels` rows are also accepted:

```json
{"text": "Alice works in Paris.", "label": [[0, 5, "PER"], [15, 20, "LOC"]]}
```

Conversion notes:

- Offset-based entities are preferred because repeated surface forms can be ambiguous.
- Word-only entities are matched in the sentence by surface form; repeated occurrences may all be labeled unless offsets are provided.
- Basic BIO conversion cannot represent overlapping or nested spans without loss; reject or simplify those spans before training.

## NER supervised DOCX

The bundled `docx2txt` converter supports a simple paragraph pattern:

```text
Sentence:本报北京9月4日讯记者杨涌报道。
PER:杨涌
LOC:北京
ORG:人民日报
Sentence:秦始皇兵马俑位于陕西省西安市。
PER:秦始皇
LOC:陕西省,西安市
```

Rules:

- A sentence paragraph starts with `Sentence:` followed by raw text.
- Entity paragraphs use `LABEL:entity1,entity2`.
- Comma-separated entity names are matched inside the current sentence.
- If entities repeat or overlap, prefer JSON with explicit offsets.

## RE supervised CSV/JSON/XLSX

DeepKE standard RE examples use one candidate pair per row. The common columns are:

```csv
sentence,relation,head,head_offset,tail,tail_offset
孔正锡，导演，2005年以一部温馨的爱情电影《长腿叔叔》敲开电影界大门,导演,长腿叔叔,23,孔正锡,0
```

Field meanings:

- `sentence`: raw sentence containing the candidate pair.
- `relation`: relation label for the pair.
- `head`: subject/head entity text.
- `head_offset`: character offset of `head` in `sentence`.
- `tail`: object/tail entity text.
- `tail_offset`: character offset of `tail` in `sentence`.

JSON should be a list of objects with the same keys. XLSX should put headers in the first sheet's first row and values in following rows. The bundled `json2csv` and `xlsx2csv` converters preserve column names instead of hard-coding only RE fields, so they can also normalize AE-style tabular files when the downstream example expects CSV.

## AE tabular data

DeepKE standard AE data is CSV-oriented. A typical prepared dataset has split files such as `train.csv`, `valid.csv`, and `test.csv`, plus a label inventory such as `attribute.csv`. Exact columns depend on the chosen AE example, so keep the first-row header stable and validate it against the target config before training.

## Weak-supervision NER dictionary

Dictionary CSV format:

```csv
entity,label
Washington,LOC
University of California,ORG
杨涌,PER
```

Rules:

- Two columns are required: entity surface form and label.
- Header names `entity,label` are recognized; two-column headerless files are also accepted.
- Include aliases, casing variants, punctuation variants, and domain abbreviations if they should be labeled.
- Longer entity strings should win over shorter overlapping strings. For example, `University of California` should be matched before `California`.

## Weak-supervision source text

Source text is a directory of `.txt` files or a single text file. Each nonempty line is treated as one sample.

```text
University of California is located in California.
秦始皇兵马俑位于陕西省西安市。
```

The generated weak-supervision helper creates BIO text split files from these lines. It does not infer new labels; it only labels dictionary matches.

## Distant-supervision RE source file

Source JSON/JSONL records must contain one candidate pair per record:

```json
[
  {
    "sentence": "The United States Embassy in Beirut, Lebanon sponsored a concert.",
    "head": "Lebanon",
    "tail": "Beirut",
    "head_offset": 38,
    "tail_offset": 30
  }
]
```

Recommended fields:

- Required: `sentence`, `head`, `tail`.
- Strongly recommended: `head_offset`, `tail_offset`.
- Optional: entity types, IDs, provenance, confidence, or any fields the downstream pipeline should preserve.

## Distant-supervision triple file

Triple CSV format:

```csv
head,tail,rel
Lebanon,Beirut,/location/location/contains
Company A,City B,/business/company/place_founded
```

Rules:

- `head` and `tail` are matched as exact strings after language-specific normalization.
- `rel` is copied into the source record's `relation` field.
- Unmatched pairs receive the configurable none label, defaulting to `None`.
- Matching is directed unless bidirectional matching is explicitly requested.

## Doccano export reminders

- NER exports should contain raw `text` plus `entities` with offsets.
- RE exports usually contain `entities` and `relations`; DeepKE standard RE is easier to feed after flattening to one candidate pair per row.
- Some RE annotation setups include the candidate pair in the text with separators such as `text*head*tail*head_type*tail_type`. Strip or consistently parse that suffix before computing offsets for the actual sentence.
