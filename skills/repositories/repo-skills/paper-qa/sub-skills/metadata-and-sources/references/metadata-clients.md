# Metadata clients

PaperQA metadata clients hydrate `DocDetails` from public scholarly metadata providers. They are useful when a user already knows a paper title or DOI, or when `Docs.aadd(...)` has extracted or received title/DOI/author hints and `settings.parsing.use_doc_details` is enabled.

## Core API

```python
from paperqa.clients import DocMetadataClient, DEFAULT_CLIENTS, ALL_CLIENTS

client = DocMetadataClient(metadata_clients=DEFAULT_CLIENTS)
details = await client.query(
    title="Augmenting language models with chemistry tools",
    authors=["Andres M. Bran", "Sam Cox"],
    fields=["title", "doi"],
)
```

Verified installed signatures include:

- `DocMetadataClient(http_client=None, metadata_clients=DEFAULT_CLIENTS)`.
- `DocMetadataClient.query(self, **kwargs) -> DocDetails | None`.
- `DocMetadataClient.bulk_query(self, queries, concurrency=10) -> list[DocDetails]`.
- `DocMetadataClient.upgrade_doc_to_doc_details(self, doc, **kwargs) -> DocDetails`.

Supported query hints are intentionally simple:

| Input | When to use | Notes |
| --- | --- | --- |
| `doi="10..."` | Best known identifier is a DOI. | DOI wins when both DOI and title are present. DOI URL prefixes such as `https://doi.org/` are normalized by the DOI query model. |
| `title="..."` | DOI is missing and title can be matched. | Title search requires close match; use `authors` to disambiguate duplicate or similar titles. |
| `authors=[...]` | Title-only search has ambiguous or duplicate results. | Author matching is provider-specific; Semantic Scholar manually checks title/author agreement. |
| `fields=[...]` | The task only needs selected fields. | `title` and `doi` are automatically added to title queries; `authors` is added when provided. A smaller field set can reduce provider cost and latency. |
| `title_similarity_threshold=0.75` | Advanced title matching control. | Keep the default unless the user explicitly wants looser matching and accepts false-positive risk. |

Common `DocDetails` fields to request include `title`, `doi`, `authors`, `publication_date`, `year`, `journal`, `pages`, `volume`, `issue`, `publisher`, `issn`, `url`, `doi_url`, `pdf_url`, `license`, `bibtex`, `citation_count`, `source_quality`, `is_retracted`, and `doc_id`. Provider field support varies; see provider notes below.

## Default clients versus all clients

The installed package reports:

- `DEFAULT_CLIENTS`: `CrossrefProvider`, `SemanticScholarProvider`, `JournalQualityPostProcessor`.
- `ALL_CLIENTS`: default clients plus `OpenAlexProvider`, `UnpaywallProvider`, `RetractionDataPostProcessor`.

Use `DEFAULT_CLIENTS` for ordinary metadata enrichment. It balances metadata coverage, citation counts, bibtex/citation generation, and journal quality without extra open-access/retraction provider calls.

Use `ALL_CLIENTS` only when the task needs open-access PDF/license details or retraction status and the user accepts extra network calls and rate-limit exposure. At large scale, do not start with `ALL_CLIENTS`; use explicit providers and `fields` instead.

## Provider and post-processor roles

| Component | Type | Primary contribution | Environment knobs |
| --- | --- | --- | --- |
| `CrossrefProvider` | Provider | DOI/title lookup, DOI URL, publisher, journal, pages, issue/volume, publication date, citation count, and BibTeX generation through Crossref. | `CROSSREF_API_KEY`, `CROSSREF_MAILTO`, `CROSSREF_API_REQUEST_TIMEOUT`. Missing key/mailto is allowed but may reduce rate-limit friendliness. |
| `SemanticScholarProvider` | Provider | DOI/title lookup, citation count, open-access PDF URL when available, Semantic Scholar BibTeX, arXiv DOI normalization, and author disambiguation. | `SEMANTIC_SCHOLAR_API_KEY`, `SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT`. Missing API key is allowed but may hit stricter rate limits. |
| `OpenAlexProvider` | Provider | Open-access status/details, institution/source metadata, citation count, best OA location PDF URL/license. | `OPENALEX_MAILTO`, `OPENALEX_API_KEY`, `OPENALEX_API_REQUEST_TIMEOUT`. Missing mailto may deprioritize requests. |
| `UnpaywallProvider` | Provider | Open-access status, best OA PDF URL, repository copy information, license, journal OA metadata. | `UNPAYWALL_EMAIL`, `UNPAYWALL_TIMEOUT`. A real email is more courteous than the package fallback. |
| `JournalQualityPostProcessor` | Post-processor | Adds `source_quality` from the bundled journal-quality CSV when a journal name exists. | Optional custom CSV path can be passed to the processor constructor. |
| `RetractionDataPostProcessor` | Post-processor | Adds `is_retracted` by checking a retraction DOI cache. | Optional custom retraction CSV path can be passed; if default cache is missing or expired, the processor may download retraction data. |

Providers run against DOI or title/author queries. Post-processors run after a provider returns `DocDetails`, so they need fields such as `journal` or `doi` to be present.

## Flat versus nested composition

A flat collection runs providers in the same task and aggregates the returned `DocDetails`, then runs processors on the aggregate.

```python
from paperqa.clients import CrossrefProvider, SemanticScholarProvider, JournalQualityPostProcessor

client = DocMetadataClient(
    metadata_clients=[CrossrefProvider, SemanticScholarProvider, JournalQualityPostProcessor]
)
details = await client.query(doi="10.1038/s42256-024-00832-8")
```

Use flat composition when you want provider results merged and do not need strict provider ordering.

A nested sequence creates ordered tasks. After each task, PaperQA checks whether hydration can stop. It stops early when `DocDetails.is_hydration_needed(inclusion=fields)` is false, or when all requested fields are present.

```python
client = DocMetadataClient(
    metadata_clients=[[SemanticScholarProvider], [CrossrefProvider]]
)
details = await client.query(
    doi="10.48550/arxiv.2312.07559",
    fields=["doi", "title"],
)
```

Use nested composition when a fast or preferred provider should get the first chance, and a fallback provider should run only when requested fields remain missing. Tests verify both sequential execution and early stop behavior.

Do not pass an empty provider list: `DocMetadataClient(metadata_clients=[])` raises `ValueError` because at least one `MetadataProvider` is required.

## Field selection details

Field selection is a provider hint, not a guarantee that every provider returns every field.

- Crossref maps PaperQA fields to Crossref `select` fields for title searches. It can skip separate BibTeX retrieval when `bibtex` is not requested.
- Semantic Scholar maps PaperQA fields to Graph API fields. `externalIds` is needed for DOI, and `openAccessPdf` is needed for `pdf_url`.
- OpenAlex sends selected fields directly as `select`. Tests exercise open-access checks using a narrow field request and confirm unrelated fields can remain unset.
- Unpaywall currently does not expose the same `fields` optimization in its provider methods.
- `JournalQualityPostProcessor` needs `journal`; `RetractionDataPostProcessor` needs `doi`.

For fast DOI/title-only hydration, ask only for what the downstream code needs:

```python
fast_client = DocMetadataClient(metadata_clients=[[SemanticScholarProvider], [CrossrefProvider]])
details = await fast_client.query(
    title="Attention is All you Need",
    authors=["Ashish Vaswani", "Noam Shazeer"],
    fields=["title", "doi"],
)
```

If a user needs `pdf_url`, `license`, or open-access status, include OpenAlex or Unpaywall explicitly and document that the call is live-network and provider-limited.

## Metadata during document addition

`Docs.aadd(...)` accepts metadata hints:

```python
await docs.aadd(
    path="paper.pdf",
    title="Known title",
    doi="10...",
    authors=["First Author"],
    settings=settings,
)
```

When `settings.parsing.use_doc_details` is true and a title or DOI is available, `Docs.aadd` constructs a `DocMetadataClient` unless a caller passes `metadata_client`. It then calls `upgrade_doc_to_doc_details(doc, **query_kwargs)` and merges returned metadata into the document.

Important merge behavior:

- Caller-provided `title`, `doi`, `authors`, or other `DocDetails` fields are preserved through a `provided_doc_details + provider_doc_details` merge.
- `fields_to_overwrite_from_metadata` controls whether metadata can overwrite generated `docname`, `dockey`, `doc_id`, `key`, `citation`, and `content_hash` fields.
- If no provider result is found, `upgrade_doc_to_doc_details` returns a `DocDetails` derived from the original `Doc` plus any explicitly provided fields.
- For local parser behavior after metadata hydration, switch to the `docs-and-parsing` sub-skill.

## Result interpretation

`DocDetails.formatted_citation` adds warnings and context when hydrated fields are present:

- If `is_retracted` is true, the formatted citation starts with `**RETRACTED ARTICLE**` and includes retraction provenance text.
- If both `citation_count` and `source_quality` exist, the formatted citation includes citation count and journal-quality message.
- `SOURCE_QUALITY_MESSAGES` maps quality scores: `0` poor quality or predatory journal, `1` peer-reviewed journal, `2` domain-leading peer-reviewed journal, `3` highest quality peer-reviewed journal. `-1` means undefined/unknown.

Do not overstate metadata as ground truth. Treat provider data as external metadata that may be stale, partial, or inconsistent across providers.

## Evidence basis

This reference distills repository documentation, metadata-client implementation behavior, document-addition hydration behavior, citation/merge model behavior, native metadata-client tests, and installed package facts. VCR metadata tests are live-service candidates but are not safe no-network runtime defaults.
