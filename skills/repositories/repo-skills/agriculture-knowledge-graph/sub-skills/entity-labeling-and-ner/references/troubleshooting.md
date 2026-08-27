# Troubleshooting

## Workflow-specific failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Label file fails validation | Extra columns, empty lines, or a label outside `0-16` | Run the label checker, then fix the offending lines |
| A label file with Chinese or English terms is parsed incorrectly | The legacy reader expects whitespace-delimited pairs and is not a general CSV parser | Keep each line as exactly one term plus one integer label |
| `get_NE` returns a POS-style tag instead of a numeric label | The token was not found in the predicted-label map or not present in Neo4j | Check both the mapping file and the entity source data |
| `get_NE` returns `0` too often | The token fails the POS filters or the DB lookup | Confirm THULAC output, the candidate span, and the Neo4j item list |
| KNN import succeeds but prediction is not trustworthy | The fastText model file is missing or different from the expected Chinese model | Treat the run as metadata-only unless the model file is present |
| `pyfasttext` imports but the classifier cannot load a model | The model file path is wrong or the file is not a fastText binary model | Pass the correct model path or stay in probe mode |
| Label statistics do not match expectations | Manual labels and predicted labels are easy to confuse | Inspect the exact file path before editing or reading counts |
| Preload import is slow or touches services | The preload module opens THULAC, Neo4j, MongoDB, vectors, and tree resources at import time | Avoid importing preload in minimal tests unless the environment is ready |
| KNN similarity results look unstable | The legacy normalization and variance code is fragile | Use the probe for inspection and review the similarity path before trusting output |

## Safe recovery steps

1. Validate the label file.
2. Confirm the target file is the correct one for the workflow.
3. Check whether the task needs only offline labels or also the fastText model.
4. If the task is only to inspect features, use the bundled feature probe instead of running the classifier.
5. If the task needs live NER, make sure the backing graph data and labels are available.

## What not to do

- Do not download a large model just to inspect file formats.
- Do not assume predicted labels and manual labels are interchangeable.
- Do not treat a provisional THULAC tag as a final numeric classification.
- Do not use the NER workflow as a substitute for relation labeling.
