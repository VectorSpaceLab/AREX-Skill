# Clinical trials and literature sources

This reference covers PaperQA's external source helpers: ClinicalTrials.gov, OpenReview, Zotero, and paper acquisition guidance. These workflows can perform network calls, downloads, model calls, or credentialed API access. Ask before running them and keep secrets out of code, logs, prompts, and generated files.

## ClinicalTrials.gov search

PaperQA has a native `clinical_trials_search` agent tool. It is not enabled in the default tool list, but named settings are bundled for common workflows.

Installed facts report these named settings:

| Setting | Tool names | Best use |
| --- | --- | --- |
| `Settings.from_name("search_only_clinical_trials")` | `clinical_trials_search`, `gather_evidence`, `gen_answer`, `complete` | Answer only from live ClinicalTrials.gov search results, with no paper search tool. |
| `Settings.from_name("clinical_trials")` | `clinical_trials_search`, `paper_search`, `gather_evidence`, `gen_answer`, `complete` | Combine normal PaperQA paper search/evidence with ClinicalTrials.gov search. |

Example configuration pattern:

```python
from paperqa import Settings, agent_query

answer_response = await agent_query(
    query="What drugs have been found to effectively treat Ulcerative Colitis?",
    settings=Settings.from_name("search_only_clinical_trials"),
)
print(answer_response.session.formatted_answer)
```

To add clinical trial search to a custom tool set:

```python
from paperqa import Settings
from paperqa.agents.tools import DEFAULT_TOOL_NAMES

settings = Settings(
    agent={"tool_names": DEFAULT_TOOL_NAMES + ["clinical_trials_search"]},
)
```

The installed signature for the lower-level source helper is:

```python
add_clinical_trials_to_docs(query, docs, settings, limit=10, offset=0, client=None) -> tuple[int, int, str | None]
```

It searches ClinicalTrials.gov, retrieves study JSON, formats each trial as a `DocDetails`, adds one text per trial to `Docs`, and adds a metadata text noting total search results. The tuple is `(total_result_count, new_result_count, error_message)`.

### Clinical trial query syntax

The `clinical_trials_search` tool accepts the ClinicalTrials.gov v2 query syntax through a single string. Useful patterns include:

- Basic term search: `heart attack`.
- Exact phrase: `EXPANSION[None]COVERAGE[FullMatch]"exact phrase"`.
- Field search: `AREA[InterventionName]aspirin` or `AREA[Phase]PHASE3`.
- Location grouping: use a `SEARCH` location group such as ``cancer AND SEARCH\[Location\](AREA\[LocationCity\]Boston AND AREA\[LocationState\]Massachusetts)``.
- Boolean logic: `(cancer OR tumor) AND NOT AREA[StdAge]CHILD`.
- Date ranges: `AREA[ResultsFirstPostDate]RANGE[2015-01-01, MAX]`.

Invalid field enum values can return HTTP 400 with plain-text parser errors. Do not blindly retry a 400; simplify or correct the query.

### Clinical trial formatting

`format_to_doc_details(trial_data)` creates `DocDetails` with:

- `title`: brief title.
- `docname` and `dockey`: NCT id.
- `authors`: responsible investigator when present.
- `year`: year extracted from start date.
- `citation`: investigator, title, organization, year, and `ClinicalTrials.gov Identifier: NCT...`.
- `other.client_source`: `clinicaltrials.gov`.

`parse_clinical_trial(json_data)` creates a human-readable text view with sections for trial information, status, description, design, and eligibility. PaperQA uses raw JSON by default; set `settings.parsing.use_human_readable_clinical_trials = True` when a readable text form is preferred.

The bundled script `../scripts/mock_clinical_trials_format.py` performs a no-network check with sample trial data and verifies both NCT and citation signals.

### Clinical trial partitioning in agent evidence

When `clinical_trials_search` is enabled, PaperQA changes evidence handling so clinical-trial contexts can be counted separately from ordinary paper contexts. The environment status can report paper count, relevant papers, clinical trial count, relevant clinical trials, evidence count, and current cost.

## OpenReview helper

`paperqa.contrib.openreview_paper_helper.OpenReviewPaperHelper` supports venue-based OpenReview workflows:

- `OpenReviewPaperHelper(settings, venue_id="ICLR.cc/2025/Conference", username=None, password=None)`.
- `get_venues()` lists OpenReview venues.
- `get_submissions()` retrieves submissions for the selected venue.
- `fetch_relevant_papers(question)` asks an LLM to select relevant submissions and downloads their PDFs.
- `aadd_docs(subs=None, docs=None)` adds downloaded PDFs to a `Docs` object, using OpenReview metadata for citation/title/authors when available.

Prerequisites and cautions:

- Requires the optional `openreview` extra (`paper-qa[openreview]`) and the `openreview-py` package.
- Uses `OPENREVIEW_USERNAME` and `OPENREVIEW_PASSWORD` when credentials are not passed directly.
- `Settings.from_name("openreview")` is a convenience profile, but it uses model and embedding settings that may require separate provider credentials.
- `fetch_relevant_papers` performs OpenReview API calls, LLM calls, and PDF downloads. Ask before running it.
- The helper writes PDFs under `settings.agent.index.paper_directory`; ensure the user has chosen a writable output directory.

## Zotero helper

`paperqa.contrib.ZoteroDB` wraps `pyzotero` to iterate over a user's Zotero library and download PDF attachments.

Constructor highlights:

```python
from paperqa.contrib import ZoteroDB

zotero = ZoteroDB(library_type="user")  # or library_type="group"
```

Prerequisites and behavior:

- Requires the optional `zotero` extra (`paper-qa[zotero]`) and `pyzotero`.
- Requires `ZOTERO_USER_ID` and `ZOTERO_API_KEY` unless passed as constructor arguments.
- API key must have read access to the target library.
- Zotero items must have PDF attachments. The helper skips items with no PDF attachment.
- By default PDFs are cached under PaperQA's Zotero cache directory; users can pass a `storage` directory.
- The helper parses downloaded PDFs with `paperqa_pymupdf.parse_pdf_to_pages` by default, so parser dependencies matter.

Iteration supports search and pagination arguments such as `limit`, `start`, `q`, `qmode`, `since`, `tag`, `sort`, `direction`, and `collection_name`. Do not combine `collection_name` with search query arguments; the helper raises a `ValueError` for that combination.

Common operating pattern:

```python
from paperqa import Docs
from paperqa.contrib import ZoteroDB

docs = Docs()
zotero = ZoteroDB(library_type="user")
for item in zotero.iterate(q="large language models", qmode="everything", limit=20):
    if item.num_pages > 30:
        continue
    await docs.aadd(item.pdf, docname=item.key)
```

For `Docs.aadd` and querying after PDF ingestion, switch to `docs-and-parsing` and `agentic-rag` respectively.

## Where to get papers safely

Preferred paths:

1. User supplies PDFs, text files, or authorized open-access URLs.
2. Use metadata clients to discover DOI, open-access status, license, and `pdf_url` when the user wants provider lookups.
3. Use Zotero for the user's own library when API credentials and PDF attachments are available.
4. Use OpenReview for venues when credentials/download permission and output directory are clear.
5. Use institutional/library access only under the user's policies.

Do not suggest unsafe scraping or credentialed commands as defaults. The repository documentation mentions a third-party paper-scraper project only with a caution that scraping may violate publisher rights or be legally gray. Treat that as a legal warning, not as an endorsed default workflow.

## Evidence basis

This reference distills repository clinical-trial and paper-acquisition tutorials, source helper implementations for ClinicalTrials.gov, OpenReview, and Zotero, native clinical-trial tests, and installed package facts.
