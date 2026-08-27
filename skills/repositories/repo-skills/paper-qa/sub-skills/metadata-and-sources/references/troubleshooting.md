# Metadata and source troubleshooting

Use this guide before retrying networked metadata or source workflows. Many failures are provider-side, credential-related, or query-shape problems rather than PaperQA bugs.

## Network, HTTP, TLS, and rate limits

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Metadata client returns `None` for a known DOI/title. | Provider did not find a match, timeout, transient HTTP client error, or retry exhaustion. `DOIOrTitleBasedProvider` logs warnings and returns `None` for these graceful failures. | Verify DOI/title spelling; add `authors` for title search; request fewer `fields`; try a different provider list; inspect logs at debug/warning level. |
| 403 from Semantic Scholar, Crossref, OpenAlex, or Unpaywall. | Missing key/mailto/email, quota/rate limit, provider policy block, or intermittent service protection. | Add the provider's documented env var only if the user has credentials; slow down/constrain concurrency; retry later. Do not bypass provider rules. |
| 429 or repeated timeout. | Provider rate limit, service downtime, or too broad `ALL_CLIENTS` use. | Prefer `DEFAULT_CLIENTS`, nested fallback providers, narrow `fields`, and lower concurrency for `bulk_query`. |
| TLS/connect errors. | Provider/network TLS issue or environment proxy issue. | Retry later or use a configured HTTP client only if the user has approved network settings. Do not disable TLS verification as a default. |
| Crossref response is HTML or invalid JSON. | Provider returned non-JSON error page or rate-limit page. | Treat as provider failure; retry later with `CROSSREF_MAILTO`/`CROSSREF_API_KEY` if available. |

Provider-specific environment knobs:

- Crossref: `CROSSREF_API_KEY`, `CROSSREF_MAILTO`, `CROSSREF_API_REQUEST_TIMEOUT`.
- Semantic Scholar: `SEMANTIC_SCHOLAR_API_KEY`, `SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT`.
- OpenAlex: `OPENALEX_MAILTO`, `OPENALEX_API_KEY`, `OPENALEX_API_REQUEST_TIMEOUT`.
- Unpaywall: `UNPAYWALL_EMAIL`, `UNPAYWALL_TIMEOUT`.

Never print credential values in user-facing output.

## Provider field mismatches

Symptoms:

- Requested `fields` are missing from `details`.
- `source_quality` remains `None` or unknown.
- Open-access fields appear in `details.other` rather than top-level fields.
- `pdf_url` is missing despite open-access expectations.

Actions:

1. Confirm the provider supports the field. Crossref, Semantic Scholar, OpenAlex, and Unpaywall expose different field sets.
2. Include post-processor prerequisites: `JournalQualityPostProcessor` needs `journal`; `RetractionDataPostProcessor` needs `doi`.
3. Include OpenAlex or Unpaywall only when open-access/license/PDF location is required.
4. Inspect `details.other.get("client_source")` to see which providers contributed.
5. For title queries, pass `authors` and keep a reasonable `title_similarity_threshold` to reduce false matches.

## No metadata results

Checklist:

- Use DOI when available; DOI searches are less ambiguous than title searches.
- Normalize DOI by removing whitespace and obvious URL wrappers. PaperQA strips common DOI URL prefixes, but it cannot repair arbitrary malformed IDs.
- For title-only queries, use an exact title and at least one known author.
- Avoid overly narrow field requests if downstream needs post-processing fields.
- Try nested fallback composition, for example Semantic Scholar first, Crossref second, or vice versa depending on the source type.
- If all providers fail, proceed with caller-provided citation/title/DOI and mark metadata as unresolved instead of inventing fields.

## ClinicalTrials.gov failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Tool returns `Error in clinical trial query syntax: ...`. | `add_clinical_trials_to_docs` caught an exception from search/retrieval. | Read the returned message; fix syntax before retrying. |
| HTTP 400 with plain text parser error. | Malformed ClinicalTrials.gov v2 query, unsupported enum, bad `AREA[...]`, or invalid operator nesting. | Simplify to a basic term query; validate enum spelling such as `RECRUITING`, `COMPLETED`, `PHASE3`; add operators gradually. |
| 403 in hosted/CI environments. | ClinicalTrials.gov TLS behavior or service-side blocking. PaperQA uses a TLS 1.2 max-version SSL context for its default client to avoid known 403 cases. | Retry with the built-in client path; do not disable verification. If a custom client is supplied, ensure it respects provider/TLS requirements. |
| Results found but answer ignores trials. | Evidence not gathered from clinical-trial texts, or tool not included. | Use `Settings.from_name("clinical_trials")` or `Settings.from_name("search_only_clinical_trials")`; ensure `clinical_trials_search`, `gather_evidence`, `gen_answer`, and `complete` are in tool names. |
| Trial text is hard to read. | Default storage uses raw JSON text. | Set `settings.parsing.use_human_readable_clinical_trials = True` when readability is more important than raw JSON fidelity. |

## OpenReview failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ImportError` for OpenReview. | Optional `openreview` extra is not installed. | Ask before installing `paper-qa[openreview]`; do not make it a default dependency. |
| Authentication failure. | Missing or wrong `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD`, or credentials passed incorrectly. | Ask the user to configure credentials securely. Do not request secret values in chat unless the environment's secret channel is appropriate. |
| `get_submissions` returns empty. | Wrong `venue_id` or OpenReview API change. | Use `get_venues()` to inspect available venue IDs after the user approves network calls. |
| PDF download failures. | PDF link missing, access blocked, network failure, or OpenReview response not OK. | Keep failed downloads explicit; do not fabricate local PDFs. Retry only with user-approved network access. |
| LLM selection fails. | `fetch_relevant_papers` calls a configured LLM and requires provider credentials. | Verify model settings in `settings-and-configuration`; for metadata-only tasks, avoid LLM-based paper selection. |

## Zotero failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ImportError` for Zotero. | Optional `zotero` extra / `pyzotero` is not installed. | Ask before installing `paper-qa[zotero]`. |
| `ZOTERO_USER_ID not set` or `ZOTERO_API_KEY not set`. | Required env vars are missing and constructor args were not provided. | Ask user to set env vars or pass parameters securely. Do not expose key values. |
| No items or missing PDFs. | Query filters too strict, library ID/type wrong, item has no PDF attachment, or read permission is missing. | Test a smaller `limit`, remove filters, check `library_type`, and ask user to ensure Zotero items have PDF attachments. |
| Duplicate or skipped PDFs. | The helper filters items without PDFs and duplicate PDF paths. | Report skipped items; do not assume every Zotero citation has a downloadable PDF. |
| Parser error after download. | Default parser in `ZoteroDB` uses a PDF parser; optional parser dependencies or corrupt PDFs can fail. | Route parser diagnosis to `docs-and-parsing`. |

## Retraction and journal quality issues

- Journal quality only runs when a journal name exists and can be matched against the bundled CSV. `-1` means undefined/unknown quality, not proof that a venue is bad.
- Retraction status requires a DOI. If using a custom or missing retraction CSV, `RetractionDataPostProcessor` may need to download or load the dataset. Ask before live downloads.
- A retraction warning in `formatted_citation` should be preserved verbatim and surfaced to the user.

## Legal and policy caution for third-party scrapers

Do not recommend scraping as a default method for obtaining papers. Third-party paper scrapers may violate publisher rights, license terms, robots policies, or institutional rules. If a user explicitly asks about a scraper, explain the legal/policy risk and prefer authorized alternatives: user-supplied PDFs, open-access provider links, Zotero library access, OpenReview downloads, institutional APIs, or direct publisher/library access under the user's rights.
