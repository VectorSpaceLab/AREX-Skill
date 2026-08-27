# Entity labeling and NER workflow

This workflow covers three closely related tasks:

1. THULAC-based entity recognition in text.
2. Numeric agricultural label assignment.
3. KNN-based label prediction for Hudong items.

## End-to-end flow

### 1. Preload shared resources

The legacy demo preloads:

- THULAC for segmentation and POS/NER tags
- a Neo4j connection
- the predicted-label mapping file
- word vectors
- a tree resource
- MongoDB handles used by other demo pages

Important behavior: importing the preload module has side effects. It is not a pure utility import.

### 2. Run THULAC tokenization

The recognizer splits text into token/tag pairs.

The helper logic then checks each token and some adjacent token pairs.

#### POS filters

- `preok`: broad filter for the token before a candidate span
- `nowok`: stricter filter for the current token
- `temporaryok`: tags that may be passed through as provisional entity-like spans

### 3. Map a token or token pair to a numeric label

For each candidate span:

1. Look up the span in the predicted-label dictionary.
2. Confirm the token exists in Neo4j as a Hudong item.
3. Apply the POS filters.
4. Return the numeric label if all checks pass.
5. Otherwise fall back to a provisional POS tag or label `0`.

The output meaning is:

- `1-16`: recognized entity with a known agricultural label
- `0`: non-entity or rejected candidate
- string tags such as `np`, `ns`, `ni`, `nz`: provisional named-entity-like output when the DB-backed label is missing

## Manual and seed label workflow

### Manual labels

The label-entry page appends accepted labels to `demo/label_data/labels.txt`.

The workflow is intentionally simple:

- choose an unlabeled title
- pick a numeric label
- append the `title label` line

### Seed labels

`demo/label_data/tagging_seed.py` generates seed files from `word_list.txt`.

The script is a heuristic bootstrapper, not a final classifier. It writes candidate files such as:

- `invalid.txt`
- `invalid2.txt`
- `person.txt`
- `location.txt`
- `organization.txt`
- `Political_economy.txt`
- `Animal.txt`
- `Plant.txt`
- `Chemicals.txt`
- `Climate.txt`
- `foodItem.txt`
- `disease.txt`
- `Nutrients.txt`
- `Agricultural_implements.txt`
- `Technology.txt`
- `sieve_labels.txt`

These names live in the `demo/label_data/handwork/` subtree in the source repo, while the combined manual-label file is `demo/label_data/labels.txt`.

## KNN label prediction workflow

### Inputs

- labeled Hudong items from Neo4j
- a whitespace-delimited label file
- a fastText model file such as `wiki.zh.bin`

### Outputs

- predicted `title label` files
- optional vector dumps created from the same title list

### Core similarity signal

The classifier combines:

- title similarity
- open-type list similarity
- base-info key overlap
- base-info value overlap

The numeric label is then chosen by KNN voting over the top neighbors.

## Safe usage pattern

- Use the validator before editing or appending a label file.
- Use the feature probe when you want to inspect the non-model prerequisites without downloading a fastText model.
- Use the taxonomy reference to keep manual labels, predicted labels, and sample files aligned.

## Boundaries

- UI route handling belongs to the sibling web-app sub-skill.
- Neo4j import/query belongs to the sibling graph-query sub-skill.
- Relation-sentence dataset labeling belongs to the sibling relation-extraction sub-skill.
