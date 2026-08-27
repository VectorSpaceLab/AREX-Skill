# Cross-cutting Troubleshooting

## No local dataset files

**Symptom:** The user asks where the train/dev/test files are in this skill or
expects a local dataset path.

**Cause:** This skill bundles only catalogue metadata and a search helper. It
never bundles external datasets.

**Recovery:** Use `scripts/search_dataset_index.py` to identify the upstream URL,
then tell the user that downloading requires a separate permission/license check.

## Search helper returns no matches

**Symptom:** `search_dataset_index.py --query <term>` prints `No matches`.

**Likely causes:** English/Chinese spelling mismatch, acronym variation,
category mismatch, or a dataset listed under a broader corpus category.

**Recovery:**

1. Search a shorter acronym or provider name.
2. Try a Chinese category name or canonical slug such as `text-matching`.
3. Remove `--language` because many rows have unspecified language signals.
4. Read `catalogue-overview.md` for category ownership and duplicate handling.

## Blank or confusing license field

**Symptom:** The catalogue row has an empty license, a slash, or text that does
not look like a license.

**Cause:** The original catalogue often stores incomplete license metadata.

**Recovery:** Treat the license as unknown, cite the provider/source URL, and
require upstream verification before download, redistribution, commercial use,
or publication.

## Broken, stale, or permissioned links

**Symptom:** A link returns 404, requires login, asks for a password, or points
to a competition page with no visible data.

**Recovery:** Report the catalogue row as a candidate rather than a guaranteed
source. Search for the current provider page, paper, or GitHub repository only
if the downstream task authorizes network exploration.

## Duplicate dataset names

**Symptom:** A query returns the same title under more than one category, or a
well-known dataset appears in both QA and reading-comprehension contexts.

**Recovery:** Preserve the category slug and task reason in the answer. Compare
what the user wants to do: answer extraction, question-answer matching,
classification, pretraining, or generation.

## Non-ASCII paths and names

**Symptom:** A shell command or JSON consumer mishandles category names such as
`文本分类` or `阅读理解`.

**Recovery:** Use category slugs in scripts (`text-classification`,
`reading-comprehension`) and keep Chinese names in presentation only. Ensure
files are read and written as UTF-8.

## Malformed Markdown links in source-derived metadata

**Symptom:** A URL or title in the index looks odd, has nested brackets, or
includes password text.

**Cause:** Some source table rows used malformed Markdown or inline notes.

**Recovery:** Treat the entry as best-effort catalogue metadata. Use the title,
provider, keywords, and paper URL as search clues; do not rely on exact link
syntax without external verification.
