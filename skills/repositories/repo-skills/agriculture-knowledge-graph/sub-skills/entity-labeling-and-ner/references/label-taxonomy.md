# Label taxonomy

This repository uses a fixed numeric entity taxonomy for agricultural labeling and NER. Label files are whitespace-delimited pairs of:

- `term`
- `label`

The label must be an integer from `0` to `16`.

## Canonical label map

| Label | Name | Typical meaning |
| --- | --- | --- |
| 0 | Invalid | Not a concrete entity, or noisy data |
| 1 | Person | People and positions |
| 2 | Location | Places, regions, administrative units |
| 3 | Organization | Institutions, meetings, journals |
| 4 | Political economy | Policy, economics, political terms |
| 5 | Animal | Livestock, birds, fish, other animals |
| 6 | Plant | Crops, fruits, vegetables, herbs, fungi, plant parts |
| 7 | Chemicals | Fertilizer, pesticide, fungicide, chemicals, technical chemistry terms |
| 8 | Climate | Weather, climate, seasons, solar terms |
| 9 | Food items | Products derived from plants or animals |
| 10 | Diseases | Plant or animal diseases |
| 11 | Natural disaster | Disasters, pollution, other destructive natural events |
| 12 | Nutrients | Fat, minerals, vitamins, carbohydrates, salts |
| 13 | Biochemistry | Organs, tissues, genes, cells, microbes, biological terms |
| 14 | Agricultural implements | Machines or physical tools used in agriculture |
| 15 | Technology | Agricultural techniques, measures, and related terms |
| 16 | Other entity | Named entities outside the agricultural core but still entities |

## Source-file conventions

Common label files in this repo include:

- `labels.txt`
- `predict_labels.txt`
- `demo/label_data/labels.txt`
- `demo/toolkit/predict_labels.txt`
- `KNN_predict/labels.txt`
- `KNN_predict/predict_labels.txt`
- `KNN_predict/predict_labels2.txt`

The manual-label workflow appends to the `demo/label_data/labels.txt` family, while the prediction workflow writes predicted labels to a separate file.

## Validation rules

The bundled validator checks that:

- each nonblank line has exactly two whitespace-separated fields;
- the second field parses as an integer;
- the integer is between `0` and `16` inclusive.

Recommended additional checks:

- reject duplicate `term` entries unless a task explicitly wants to inspect collisions;
- flag label `0` rows separately when looking for candidate entities;
- ensure the file path matches the intended workflow, because manual labels and predicted labels are easy to confuse.
