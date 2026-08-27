# QA and Reading Troubleshooting

## SQuAD, NewsQA, or WikiQA appears more than once

The catalogue lists some well-known English datasets in both QA-oriented and
reading-comprehension-oriented contexts. Preserve category and version details
in the answer, especially SQuAD1.0 vs SQuAD2.0.

## User asks for Chinese legal QA

Check whether they need reading comprehension (`qa-reading`: CJRC/CAIL) or
semantic case matching (`matching-nli`: CAIL SCM). Legal resources often have
competition-specific terms.

## Medical QA data terms are unclear

Treat cMedQA/webMedQA rows as sensitive and require upstream license/privacy
verification before training or redistribution.

## DuReader variant ambiguity

DuReader, Robust, Checklist, YesNo, and 2.0 are different evaluation surfaces.
Search all `dureader` entries and choose by the user's answer type, robustness,
or fine-grained evaluation need.
