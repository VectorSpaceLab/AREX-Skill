# Discovery and Download Workflows

These recipes are safe patterns for finding URLs and retrieving pages before handing HTML to extraction/output workflows. Prefer discovery with `--list` or Python URL lists first, review/filter the candidates, then download and extract in a separate step.

## 1. Choose the right entry point

| Goal | Use | Why |
| --- | --- | --- |
| One URL, decoded HTML only | `fetch_url(url)` | Short and applies response suitability checks. |
| Status, headers, final redirect URL, or raw bytes | `fetch_response(url, decode=True, with_headers=True)` | Keeps the full `Response` object. |
| Many URLs across domains | `UrlStore` + `load_download_buffer()` + `buffered_downloads()` | Domain-aware throttling and parallelism. |
| Feed item discovery | `find_feed_urls()` or `trafilatura --feed ... --list` | Finds Atom/RSS/JSON feed URLs and items. |
| Sitemap URL discovery | `sitemap_search()` or `trafilatura --sitemap ... --list` | Handles robots.txt, common guesses, nested sitemaps, text sitemaps, and `hreflang`. |
| Internal link frontier | `focused_crawler()` or `trafilatura --crawl ...` | Docs-supported focused crawler with robots/crawl-delay handling. |
| Discovery plus crawl fallback | `trafilatura --explore ...` | Tries sitemaps first, crawls domains where discovery finds nothing. |
| URL quality probing | `trafilatura --probe ...` | Downloads candidates and prints URLs with usable extractable text. |

## 2. Single page download

### Python: decoded page only

```python
from trafilatura.downloads import fetch_url

url = "https://example.org/article"
html = fetch_url(url)
if html is None:
    raise RuntimeError(f"Download failed or page was unsuitable: {url}")

print(html[:200])
```

### Python: inspect status, headers, final URL, and bytes

```python
from trafilatura.downloads import fetch_response

response = fetch_response(
    "https://example.org/article",
    decode=True,
    with_headers=True,
)
if response is None:
    raise RuntimeError("request failed")

print(response.status)
print(response.url)             # final/effective URL after redirects
print(response.headers or {})
print(response.html[:200] if response.html else response.data[:200])
```

### CLI: one URL

```bash
# Fetch, extract, and print text to stdout.
trafilatura -u "https://example.org/article"

# Preserve the downloaded HTML while writing extracted output.
trafilatura -u "https://example.org/article" -o output/ --backup-dir htmlbackup/
```

Validation checklist:

- `fetch_url()` returning `None` means either download failure, non-200 status, or active size/suitability constraints rejected the response.
- Use `fetch_response()` when you need to separate network success from extraction suitability.
- Record final `response.url` when redirects matter for deduplication or provenance.

## 3. Custom timeout, size, cookies, user agent, and sleep settings

Use a config file for CLI or `use_config()` for Python. Important settings include `DOWNLOAD_TIMEOUT`, `SLEEP_TIME`, `MAX_FILE_SIZE`, `MIN_EXTRACTED_SIZE`, `MIN_OUTPUT_SIZE`, `USER_AGENTS`, `COOKIE`, and `EXTERNAL_URLS`.

### Python config snippet

```python
from trafilatura.downloads import fetch_url
from trafilatura.settings import use_config

config = use_config()
config.set("DEFAULT", "DOWNLOAD_TIMEOUT", "15")
config.set("DEFAULT", "SLEEP_TIME", "10")
config.set("DEFAULT", "MAX_FILE_SIZE", "5000000")
config.set("DEFAULT", "USER_AGENTS", "MyCrawler/1.0")
config.set("DEFAULT", "COOKIE", "consent=yes")

html = fetch_url("https://example.org/page", config=config)
```

### CLI config usage

```bash
trafilatura -i urls.txt -o output/ --config-file settings.cfg
```

Minimal `settings.cfg` fragment:

```ini
[DEFAULT]
DOWNLOAD_TIMEOUT = 15
SLEEP_TIME = 10
MAX_FILE_SIZE = 5000000
USER_AGENTS = MyCrawler/1.0
COOKIE = consent=yes
EXTERNAL_URLS = off
```

## 4. Polite batch download queue

This pattern keeps many domains active in parallel while spacing requests per domain.

```python
from courlan import UrlStore
from trafilatura.downloads import add_to_compressed_dict, buffered_downloads, load_download_buffer

seed_urls = [
    "https://example.org/article-1",
    "https://example.net/story",
    "https://example.org/article-2",
]

# Optional filters: blacklist normalized URLs and keep only matching path substrings.
blacklist = {"example.org/private"}
url_filter = ["/article", "/story"]

url_store = add_to_compressed_dict(seed_urls, blacklist=blacklist, url_filter=url_filter)
errors = []
threads = 4
sleep_time = 5.0

while not url_store.done:
    bufferlist, url_store = load_download_buffer(url_store, sleep_time=sleep_time)
    for url, html in buffered_downloads(bufferlist, threads):
        if html is None:
            errors.append(url)
            continue
        # Hand html to extraction/output workflow, or save it for later.
        print(url, len(html))

print(f"failed: {len(errors)}")
```

Response-object variant:

```python
from trafilatura.downloads import buffered_response_downloads, load_download_buffer

bufferlist, url_store = load_download_buffer(url_store, sleep_time=5.0)
for url, response in buffered_response_downloads(bufferlist, download_threads=4):
    if response is None:
        print("failed", url)
    else:
        print(url, response.status, response.url, len(response.data or b""))
```

CLI equivalent:

```bash
# Read URLs, download/extract with domain-aware throttling, and write outputs.
trafilatura -i urls.txt -o extracted/ --backup-dir htmlbackup/ --parallel 4

# Only print the input/discovered URLs without downloading/extracting.
trafilatura -i urls.txt --list
```

Batch validation:

- Verify the input list contains one URL per line and only URLs you are permitted to request.
- Start with `--list` or print `url_store.dump_urls()` to confirm filtering before network calls.
- Use conservative `SLEEP_TIME` for a small number of domains; parallelism is most helpful across many domains.
- Keep failed URLs for retry, archive fallback, or predownloaded HTML processing.

## 5. Discover URLs with feeds

### CLI: inspect feed-discovered links without downloading pages

```bash
# Discover feed item URLs from a homepage.
trafilatura --feed "https://example.org/" --list

# Discover from a known feed URL.
trafilatura --feed "https://example.org/feed.xml" --list

# Discover feeds for many seeds in parallel.
trafilatura -i seed-sites.txt --feed --list --parallel 4 > feed-links.txt

# Language/path filter during discovery.
trafilatura --feed "https://example.org/" --list --target-language en --url-filter /news /blog
```

If `--list` is omitted, Trafilatura downloads and processes the discovered pages immediately in the selected output format.

### Python: feed discovery from homepage or feed URL

```python
from trafilatura.feeds import find_feed_urls

links = find_feed_urls(
    "https://example.org/blog/",
    target_lang="en",
    external=False,
    sleep_time=2.0,
)

for link in links:
    print(link)
```

### Python: parse predownloaded feed/homepage without live network

```python
from trafilatura.feeds import FeedParameters, determine_feed, extract_links

params = FeedParameters(
    baseurl="https://example.org",
    domain="example.org",
    reference="https://example.org/blog/",
    external=False,
    target_lang=None,
)

homepage_html = '''<html><head>
<link rel="alternate" type="application/rss+xml" href="/feed.xml">
</head></html>'''
feed_urls = determine_feed(homepage_html, params)

feed_xml = '''<?xml version="1.0"?><rss><channel>
<link>https://example.org/blog/post-1</link>
</channel></rss>'''
article_urls = extract_links(feed_xml, params)
```

Feed validation:

- Inspect whether discovered feed URLs are comment feeds or section feeds you do not want.
- Same/similar-domain filtering is default. Set `external=True` only when external URLs are expected and permitted.
- Use URL filters to restrict broad feeds to article paths.

## 6. Discover URLs with sitemaps

### CLI: sitemap discovery first, download later

```bash
# Homepage: robots.txt + guesses + nested sitemap discovery.
trafilatura --sitemap "https://example.org/" --list > sitemap-links.txt

# Known sitemap URL.
trafilatura --sitemap "https://example.org/sitemap.xml" --list > sitemap-links.txt

# Language-targeted sitemap URLs.
trafilatura --sitemap "https://example.org/" --list --target-language de > de-links.txt

# Path/section filtering.
trafilatura --sitemap "https://example.org/" --list --url-filter /news/ /article/ > article-links.txt
```

### Python: sitemap discovery

```python
from trafilatura.sitemaps import sitemap_search

links = sitemap_search(
    "https://example.org/",
    target_lang="en",
    external=False,
    sleep_time=2.0,
    max_sitemaps=1000,
)
print(len(links))
```

### Python: parse a predownloaded sitemap body

```python
from trafilatura.sitemaps import SitemapObject, extract_robots_sitemaps

robots_txt = "Sitemap: https://example.org/sitemap.xml"
sitemap_candidates = extract_robots_sitemaps(robots_txt, "https://example.org")

sitemap = SitemapObject("https://example.org", "example.org", sitemap_candidates, target_lang="en")
sitemap.current_url = "https://example.org/sitemap.xml"
sitemap.content = '''<?xml version="1.0"?>
<urlset>
  <url><loc>https://example.org/en/article-1</loc></url>
  <url><loc>https://example.org/fr/article-2</loc></url>
</urlset>'''
sitemap.process()
print(sitemap.urls)  # language heuristics keep English-looking URLs
```

Sitemap validation:

- Use `--list` and review counts before fetching every sitemap-discovered page.
- Bound `max_sitemaps` for large sites to avoid spending all budget on nested sitemap indexes.
- For very large sitemap output, filter and sample before downloading.
- If the base URL is not live, `sitemap_search()` returns an empty list; consider a predownloaded sitemap body or archived source when appropriate.

## 7. Focused crawling and resumable state

Use the focused crawler for intra-site discovery when feeds/sitemaps are absent or insufficient. It is not a general web-scale crawler.

### CLI

```bash
# Print links discovered within the website.
trafilatura --crawl "https://example.org/" > crawl-links.txt

# Explore combines sitemap discovery with crawl fallback.
trafilatura --explore "https://example.org/" --list > explored-links.txt
```

Notes:

- `--crawl` already prints discovered links; unlike feed/sitemap discovery, `--list` is not the main switch for crawler output.
- CLI crawling stops after a fixed threshold of page visits per site or exhaustion of the frontier.

### Python: incremental/resumable crawl

```python
from courlan import UrlStore
from trafilatura import spider
from trafilatura.spider import focused_crawler, is_still_navigation

# Reset global crawler state for an independent crawl in this Python process.
spider.URL_STORE = UrlStore(compressed=False, strict=False)

to_visit, known_links = focused_crawler(
    "https://example.org/",
    max_seen_urls=5,
    max_known_urls=10000,
    lang="en",
)

# Save these lists to disk if you need persistence between runs.
print("frontier", len(to_visit), "known", len(known_links), "navigation-left", is_still_navigation(to_visit))

# Resume later.
to_visit, known_links = focused_crawler(
    "https://example.org/",
    max_seen_urls=10,
    max_known_urls=10000,
    todo=to_visit,
    known_links=known_links,
    lang="en",
)
```

Crawler validation:

- Confirm the start URL scope. Starting from `https://example.org/section/` restricts links more narrowly than starting from the homepage.
- Preserve `to_visit` and `known_links` if the crawl is staged across sessions.
- Robots rules and crawl-delay are honored when available; do not override them unless you have permission and a clear reason.
- Reset `spider.URL_STORE` between unrelated crawls in the same Python interpreter.

## 8. Harvest candidate URLs without downloading content yet

This workflow supports the common two-phase pattern: gather candidates, inspect/filter/sample, then download.

```bash
# Gather candidates from sitemaps and feeds.
trafilatura --sitemap "https://example.org/" --list --target-language en --url-filter /news/ > sitemap-links.txt
trafilatura --feed "https://example.org/" --list --target-language en --url-filter /news/ > feed-links.txt

# Merge, deduplicate, and review.
sort -u sitemap-links.txt feed-links.txt > candidate-links.txt
head candidate-links.txt
wc -l candidate-links.txt

# Optional: only now download/extract, preserving HTML backups.
trafilatura -i candidate-links.txt -o extracted/ --backup-dir htmlbackup/ --parallel 4
```

Python equivalent:

```python
from trafilatura.feeds import find_feed_urls
from trafilatura.sitemaps import sitemap_search

seed = "https://example.org/"
links = set()
links.update(sitemap_search(seed, target_lang="en", external=False, max_sitemaps=500))
links.update(find_feed_urls(seed, target_lang="en", external=False))
links = sorted(url for url in links if "/news/" in url or "/article/" in url)

with open("candidate-links.txt", "w", encoding="utf-8") as fh:
    for url in links:
        fh.write(url + "\n")
```

## 9. Recover from failed downloads

### CLI archive fallback

```bash
# If direct downloads fail, retry failed URLs through the Internet Archive.
trafilatura -i urls.txt -o extracted/ --archived
```

The archive retry rewrites failed URLs to `https://web.archive.org/web/20/<original-url>` and runs the normal download/extraction pipeline on those archive snapshots.

### Python fallback pattern

```python
from trafilatura.downloads import fetch_url

url = "https://example.org/missing-page"
html = fetch_url(url)
if html is None:
    archived_url = "https://web.archive.org/web/20/" + url
    html = fetch_url(archived_url)

if html is None:
    print("still unavailable; use predownloaded HTML or skip")
```

### Download first, extract later

When network constraints are separate from extraction constraints, predownload pages externally and use Trafilatura on local files afterward:

```bash
# Example shape; choose a compliant downloader/policy for your environment.
wget --directory-prefix=download/ --wait 5 --input-file=urls.txt
trafilatura --input-dir download/ --output-dir extracted/ --xmltei --no-comments
```

Use this when you need custom network infrastructure, browser rendering, authenticated sessions, or download policies outside Trafilatura's built-in downloader.

## 10. Offline validation with bundled smoke script

From a repository root containing this generated skill tree:

```bash
python skills/disco/trafilatura/sub-skills/discovery-downloads/scripts/discovery_smoke.py
```

Expected output includes `OK discovery_smoke`. If it fails, inspect the assertion message first: most failures indicate an incompatible Trafilatura version, a missing dependency, or an API signature drift.

## Native candidates covered by these workflows

The workflows above mirror offline-safe pieces of the repository's native tests:

- `downloads_tests.py`: `Response` fields/methods, proxy plumbing, config/header handling, compressed decoding, queue creation, blacklist/filtering, buffer drawing, empty buffered response downloads.
- `feeds_tests.py`: Atom/RSS/JSON feed parsing, homepage feed-link discovery, relative feed URLs, comment-feed rejection, similar-domain/external behavior, CLI feed listing.
- `sitemaps_tests.py`: sitemap object link handling, nested sitemaps, text sitemap parsing, `hreflang`, robots sitemap extraction, invalid sitemap rejection.
- `spider_tests.py`: robots parsing, link filtering/prioritization, crawl state updates, resumable frontier/known-links behavior, crawl-delay metadata.

## Known long-tail gap

For continuous large-scale production crawling, use dedicated crawler infrastructure. Trafilatura's supported crawler is focused and intra-site oriented; it is best used to discover candidate URLs within known sites, not to run an unbounded web crawl.
