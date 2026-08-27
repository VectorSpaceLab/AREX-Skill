# Access and License Caveats

## Purpose

Read this before advising a user to download, train on, publish results from, or
redistribute a dataset discovered through this skill.

## Baseline rule

CLUEDatasetSearch is a catalogue of external resources. A row in the catalogue
is not proof that:

- the dataset is still downloadable;
- the licence permits the user's intended use;
- commercial use is allowed;
- the provider's page has not moved;
- the row's scale or split counts match the current upstream release;
- sensitive data has been removed to the user's legal or ethical standard.

## License interpretation

- A blank `license` field means **unknown**, not public domain.
- A `CC`, `Apache`, `MIT`, or `BSD` string should be rechecked at the upstream
  source because the catalogue may omit version details or split-specific terms.
- Competition datasets often require an account, competition rules, or a
  non-redistribution agreement even when the catalogue row is public.
- LDC/NIST/catalogue resources may be paid or institution-limited.
- Personal pages and cloud-drive shares may have unclear redistribution terms;
  treat them as access pointers only.

## Privacy and domain cautions

Pay special attention to:

- medical datasets such as CCKS electronic medical record NER, cMedQA, CHIP,
  and other patient/health resources;
- legal/judicial datasets such as CAIL and CJRC;
- finance, banking, and insurance datasets;
- social media corpora from Weibo or user-generated comments;
- scraped news, e-commerce, search-log, and query datasets.

For these rows, recommend verifying anonymization, consent, intended research
use, and jurisdictional constraints before model training or publication.

## Download and availability cautions

- Some links point to competition portals that may require login or close after
  a competition.
- Some rows use Baidu Pan links or extraction passwords; these are fragile and
  may fail outside mainland-China network contexts.
- Some links point to GitHub repositories that may have changed branch names,
  moved data to releases, or removed large files.
- Some rows point to paper pages but not direct data downloads.
- Large corpora and machine-translation resources can be multi-GB and should
  not be downloaded casually inside an agent session.

## Safe response pattern

When recommending a dataset, include:

1. task family and why the dataset fits;
2. language/domain/split/scale hints from the catalogue;
3. provider and source URL from the bundled index;
4. licence/access status as written, including `unknown` when blank;
5. a statement that the upstream source must be checked before download,
   redistribution, commercial use, or benchmark publication.

Example wording:

> The catalogue lists DuReader under reading comprehension with Apache-2.0 in
> the license field and a Baidu AI download page. Treat that as a candidate,
> then verify the current upstream page, split format, and licence before using
> it in a benchmark.
