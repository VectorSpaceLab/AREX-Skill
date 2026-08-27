# Sequence-labeling Troubleshooting

## User asks for local NER files

The skill has no local datasets. Return catalogue candidates and upstream links,
then require the user to supply a downloaded path before preprocessing.

## Medical NER access is unclear

CCKS medical rows have blank license cells and external competition/data pages.
Treat them as permissioned candidates and ask the user to verify access terms
before using them.

## Label format mismatch

Some rows mention BIO or BMEO, but the catalogue does not normalize schemas.
Tell the user to inspect the downloaded dataset's label file before training or
conversion.

## English NER request returns few rows

Only CoNLL-2003 is clearly English in this category. If the user needs broader
English entity corpora, use this row as a seed and perform external discovery
only if authorized.
