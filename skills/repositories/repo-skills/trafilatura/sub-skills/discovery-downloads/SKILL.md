---
name: discovery-downloads
description: "Find, filter, retrieve, and politely crawl web pages with
  Trafilatura discovery/download APIs and CLI flags."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Trafilatura Discovery and Downloads

Use this sub-skill when the task is to find candidate URLs, fetch web pages, inspect HTTP responses, or run Trafilatura's supported feed/sitemap/focused-crawl navigation before extraction.

## Best-fit tasks

- Fetch one page with `fetch_url()` or inspect status/headers/final URL with `fetch_response()`.
- Build a polite domain-aware download queue with `UrlStore`, `load_download_buffer()`, and buffered download helpers.
- Discover candidate article URLs through feeds, sitemaps, and the focused crawler.
- Use CLI navigation flags such as `--feed`, `--sitemap`, `--crawl`, `--explore`, `--probe`, `--archived`, `--url-filter`, and `--list`.
- Diagnose blocked downloads, SSL/proxy/timeouts, file-size limits, robots rules, and optional download extras.

## Read these references

1. [API reference](references/api-reference.md) for signatures, return objects, response fields, URL store behavior, and discovery helper details.
2. [Workflows](references/workflows.md) for ready-to-adapt Python and CLI recipes covering single downloads, batch queues, feeds, sitemaps, focused crawling, and Internet Archive fallback.
3. [Troubleshooting](references/troubleshooting.md) for network failures, polite throttling, proxies, SSL, optional extras, and long-tail limits.

## Bundled validation

Run the offline smoke check before relying on this sub-skill in a new environment:

```bash
python skills/disco/trafilatura/sub-skills/discovery-downloads/scripts/discovery_smoke.py
```

The script imports the discovery/download APIs, asserts key signatures, exercises `Response`, offline feed/sitemap parsing, URL filtering/queue behavior, and a mocked focused-crawl step. It does not contact the network.

## Route elsewhere

- Use the extraction/output sub-skills for HTML-to-text extraction, metadata/comments extraction, output formats, or stdin/file conversion after retrieval.
- Use the corpus-quality/deduplication coverage for text-level deduplication, corpus quality evaluation, and Simhash/fingerprints.
- Treat broad production web crawling, cross-domain frontier scheduling, anti-bot bypassing, authenticated scraping, and JavaScript rendering as out-of-scope long-tail gaps; Trafilatura provides a docs-supported focused crawler, not a full web-scale crawler.

## Evidence basis

This sub-skill is distilled from repository evidence covering download APIs, CLI navigation, feed/sitemap parsing, focused crawling, URL filtering, settings, and offline/native tests. Runtime guidance is self-contained; source paths may appear only as provenance labels in references.
