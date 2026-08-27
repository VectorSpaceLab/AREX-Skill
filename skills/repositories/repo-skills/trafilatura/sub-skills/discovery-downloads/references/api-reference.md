# Discovery and Download API Reference

This reference covers Trafilatura 2.2.0 download, feed, sitemap, and focused-crawler APIs. Import examples assume the `trafilatura` distribution is installed in the current Python environment.

## Imports by workflow

```python
from courlan import UrlStore
from trafilatura.downloads import (
    add_to_compressed_dict,
    buffered_downloads,
    buffered_response_downloads,
    fetch_response,
    fetch_url,
    load_download_buffer,
)
from trafilatura.feeds import FeedParameters, determine_feed, extract_links, find_feed_urls
from trafilatura.sitemaps import SitemapObject, extract_robots_sitemaps, sitemap_search
from trafilatura.spider import focused_crawler, is_still_navigation, parse_robots
from trafilatura.utils import Response
```

The top-level package also exposes `trafilatura.fetch_url` and `trafilatura.fetch_response`.

## Download primitives

| API | Signature | Returns | Use when |
| --- | --- | --- | --- |
| `fetch_url` | `fetch_url(url, no_ssl=False, config=DEFAULT_CONFIG, options=None)` | decoded `str` or `None` | You only need page HTML/text as Unicode and want Trafilatura's response suitability checks. |
| `fetch_response` | `fetch_response(url, *, decode=False, no_ssl=False, with_headers=False, config=DEFAULT_CONFIG)` | `Response` or `None` | You need status code, final URL after redirects, bytes, decoded HTML, or headers. |

Key behavior:

- `fetch_url()` calls `fetch_response(..., decode=True)` internally and then rejects unsuitable responses. It returns `None` for failed requests, non-200 responses, or unacceptable document sizes under the active extraction/config options.
- `fetch_response()` returns the raw response object when the request succeeds; it does not apply the same extracted-text suitability filter as `fetch_url()`.
- `no_ssl=True` disables certificate verification for the request. The urllib3 path automatically retries once with SSL disabled after an SSL error; pycurl follows equivalent SSL-error retry logic for known curl SSL error codes.
- `config` is a `ConfigParser` returned by `trafilatura.settings.use_config()`. Important defaults include `DOWNLOAD_TIMEOUT = 30`, `SLEEP_TIME = 5`, `MAX_FILE_SIZE = 20000000`, `MIN_EXTRACTED_SIZE = 250`, `MIN_OUTPUT_SIZE = 1`, and `EXTERNAL_URLS = off`.
- Optional pycurl support changes the download backend. Optional brotli/zstandard support expands accepted compressed transfer encodings and decoding.

### Response object

`Response` stores network response information with these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `data` | `bytes` | Raw response body bytes. |
| `headers` | `dict[str, str] | None` | Lower-cased HTTP headers when `with_headers=True`; otherwise `None`. |
| `html` | `str | None` | Decoded text when `decode=True` was requested or `response.decode_data(True)` was called. |
| `status` | `int` | HTTP status code returned by the download backend. |
| `url` | `str` | Effective/final URL after redirects when the backend provides it. |

Useful methods:

```python
response.decode_data(True)      # populate response.html from response.data
headers = response.headers or {}
as_dict = response.as_dict()    # includes data, headers, html, status, url
```

`bool(response)` is true when `data` is not `None`; still check `response.status`, `response.data`, and any downstream size criteria before processing.

## Domain-aware URL queues and buffered downloads

| API | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `add_to_compressed_dict` | `add_to_compressed_dict(inputlist, blacklist=None, url_filter=None, url_store=None, compression=False, verbose=False)` | `UrlStore` | Deduplicates input URLs, applies a normalized blacklist, applies substring filters, and inserts URLs into a courlan `UrlStore`. |
| `load_download_buffer` | `load_download_buffer(url_store, sleep_time=5.0)` | `(bufferlist, url_store)` | Pulls the next eligible URLs while respecting domain-aware backoff. Sleeps until URLs are eligible or the store is done. |
| `buffered_downloads` | `buffered_downloads(bufferlist, download_threads, options=None)` | generator of `(url, str_or_none)` | Parallel `fetch_url()` queue consumer. |
| `buffered_response_downloads` | `buffered_response_downloads(bufferlist, download_threads, options=None)` | generator of `(url, Response_or_none)` | Parallel `fetch_response()` queue consumer for status/final-URL/headers workflows. |

`UrlStore` is supplied by the `courlan` dependency. Common methods used by Trafilatura workflows include:

- `add_urls(urls, visited=False, appendleft=None)`: add URLs and optionally mark them visited or prioritize navigation URLs.
- `get_download_urls(time_limit=sleep_time, max_urls=...)`: draw currently eligible URLs.
- `get_url(base_or_domain, as_visited=True)`: pop one URL for a domain.
- `find_unvisited_urls(base_or_domain)` / `find_known_urls(base_or_domain)`: inspect frontier and known URLs.
- `get_known_domains()`, `total_url_number()`, `dump_urls()`, `print_unvisited_urls()`, `reset()`, and `done`.
- `store_rules(base, rules)` and `get_crawl_delay(base, default=...)` for robots/crawl-delay metadata.

Queue caveats:

- The blacklist used by `add_to_compressed_dict()` compares normalized URL strings. If building a set manually, prefer values like `example.org/path` rather than only the full scheme-qualified URL.
- `url_filter` is a list of substring patterns; a URL is kept if any pattern appears in it.
- `load_download_buffer()` can block and sleep when all remaining domains are cooling down. Use a small `sleep_time` only in tests or highly controlled environments.
- Threading helps most when the buffer contains different domains. Hammering one domain with many threads is counterproductive because domain backoff should dominate.

## Feed discovery

### Public discovery helper

```python
from trafilatura.feeds import find_feed_urls

links = find_feed_urls(
    "https://example.org/blog/",
    target_lang="en",     # optional ISO 639-1 code
    external=False,       # keep similar hosts by default
    sleep_time=2.0,       # delay before homepage fallback on failed specific URL
)
```

Signature:

```python
find_feed_urls(url, target_lang=None, external=False, sleep_time=2.0) -> list[str]
```

Behavior:

1. Determines the input domain and base URL.
2. Downloads the input URL.
3. If the content is a feed, extracts Atom/RSS/JSON-feed item links.
4. If the content is an HTML page, discovers feed URLs from `<link rel="alternate" ...>` or feed-like anchors, downloads those feeds, and extracts item links.
5. If a non-homepage URL cannot be downloaded, waits `sleep_time` and tries the homepage.
6. As a final target-language fallback, may probe Google News RSS for the domain when `target_lang` is set.
7. Filters links by URL validity, language heuristics, same/similar domain unless `external=True`, comment-feed blacklist, and any automatically derived URL filter for subpage inputs.

Lower-level feed parsing helpers are useful for offline tests or predownloaded feeds:

```python
from trafilatura.feeds import FeedParameters, determine_feed, extract_links

params = FeedParameters(
    baseurl="https://example.org",
    domain="example.org",
    reference="https://example.org/blog/",
    external=False,
    target_lang="en",
)
feed_urls = determine_feed(homepage_html, params)
article_urls = extract_links(feed_xml_or_json, params)
```

`FeedParameters` fields: `base`, `domain`, `ext`, `lang`, `ref`.

## Sitemap discovery

### Public discovery helper

```python
from trafilatura.sitemaps import sitemap_search

links = sitemap_search(
    "https://example.org/",
    target_lang="en",
    external=False,
    sleep_time=2.0,
    max_sitemaps=10000,
)
```

Signature:

```python
sitemap_search(url, target_lang=None, external=False, sleep_time=2.0, max_sitemaps=MAX_SITEMAPS_SEEN) -> list[str]
```

Behavior:

1. Determines the input domain and base URL.
2. Checks whether the base URL appears live before sitemap work.
3. Treats inputs ending in `.gz`, `sitemap`, or `.xml` as direct sitemap candidates; otherwise uses robots.txt sitemap declarations and common sitemap guesses.
4. Iterates nested sitemaps until no sitemap URLs remain or `max_sitemaps` is reached.
5. Sleeps `sleep_time` between sitemap fetches.
6. Extracts XML sitemap URLs, text-sitemap URLs, nested sitemap links, and `hreflang` alternates when `target_lang` is set.
7. Filters divergent domains unless `external=True`; whitelisted public platforms and similar domains are allowed.
8. If the original input is a subpage rather than a homepage, applies a URL substring filter derived from that subpage.

Lower-level sitemap helpers for offline parsing:

```python
from trafilatura.sitemaps import SitemapObject, extract_robots_sitemaps, is_plausible_sitemap

robots_links = extract_robots_sitemaps("Sitemap: https://example.org/sitemap.xml", "https://example.org")

sitemap = SitemapObject("https://example.org", "example.org", [], target_lang="en", external=False)
sitemap.current_url = "https://example.org/sitemap.xml"
sitemap.content = '<urlset><url><loc>https://example.org/en/page</loc></url></urlset>'
sitemap.process()
print(sitemap.urls)
```

`SitemapObject` fields: `base_url`, `content`, `current_url`, `domain`, `external`, `seen`, `sitemap_urls`, `target_lang`, `urls`.

## Focused crawler

```python
from trafilatura.spider import focused_crawler, is_still_navigation

to_visit, known_links = focused_crawler(
    "https://example.org/",
    max_seen_urls=10,
    max_known_urls=100000,
    todo=None,
    known_links=None,
    lang="en",
    rules=None,
    prune_xpath=None,
)
```

Signature:

```python
focused_crawler(homepage, max_seen_urls=10, max_known_urls=100000,
                todo=None, known_links=None, lang=None, config=DEFAULT_CONFIG,
                rules=None, prune_xpath=None) -> tuple[list[str], list[str]]
```

State and behavior:

- Returns a crawl-frontier snapshot `to_visit` and deduplicated `known_links`.
- You can resume incrementally by passing previous `to_visit` as `todo` and previous `known_links` as `known_links`.
- The crawler stores state in `trafilatura.spider.URL_STORE`. For independent crawls in one Python process, reset it with `spider.URL_STORE = UrlStore(compressed=False, strict=False)` before starting a new crawl.
- It targets internal links by base/reference URL, rejects non-crawlable URL types such as login/admin-like noise, honors robots rules when available, and prioritizes navigation pages such as tag/category/archive URLs to gather more links early.
- It fetches and parses `robots.txt` by default through `get_rules(base_url)` unless you pass a `RobotFileParser` via `rules`.
- Crawl delay comes from the URL store's robots metadata or from `config['DEFAULT']['SLEEP_TIME']`.
- `lang` uses URL and content heuristics. Full content-language checks require optional `py3langid`; when unavailable, the content-language gate is bypassed.
- `prune_xpath` removes matching nodes before extracting links; use it to ignore navigation sections or link blocks known to be irrelevant.

`is_still_navigation(to_visit)` returns `True` when the frontier still contains navigation URLs.

## CLI navigation surface

The console script is `trafilatura`. Navigation flags are mutually exclusive except where noted:

| Flag | Purpose | Typical companion flags |
| --- | --- | --- |
| `--feed [URL]` | Discover feed URLs from a homepage or extract item URLs from a feed URL. | `--list`, `-i`, `--target-language`, `--parallel`, `--url-filter` |
| `--sitemap [URL]` | Discover URLs from robots.txt, sitemap guesses, a sitemap URL, nested sitemaps, or `hreflang` alternates. | `--list`, `-i`, `--target-language`, `--parallel`, `--url-filter` |
| `--crawl [URL]` | Run the focused crawler and print discovered internal links. | `-i`, `--target-language`, `--parallel` |
| `--explore [URL]` | Combine sitemap discovery with crawl fallback for domains where sitemap/feed discovery finds nothing. | `--list`, `-i`, `--target-language`, `--url-filter`, `--parallel` |
| `--probe [URL]` | Download candidate pages and print URLs whose extracted text appears usable. | `-i`, `--target-language`, `--parallel` |
| `--archived` | On download failures in URL-processing pipelines, retry failed URLs via `https://web.archive.org/web/20/<original-url>`. | `-i` or `--URL`; also useful after discovery when not using `--list` |
| `--url-filter PATTERN ...` | Keep only URLs containing at least one substring pattern. | `--feed`, `--sitemap`, `--explore` |
| `--list` | Print discovered/input URLs without downloading and extracting them. | Especially useful with `--feed` or `--sitemap`; `--crawl` already prints links. |

Core input/output flags that commonly combine with discovery/download workflows:

- `-u/--URL URL`: fetch/process one URL.
- `-i/--input-file FILE`: read seed URLs or URL batches.
- `--input-dir DIR`: process predownloaded local files; useful after external download tools.
- `-o/--output-dir DIR`: write extracted outputs after downloading.
- `--backup-dir DIR`: preserve downloaded HTML while processing a URL list.
- `--blacklist FILE`: file of unwanted URLs to discard during processing.
- `--parallel N`: number of download/discovery threads.
- `--config-file FILE`: override settings such as timeouts, file sizes, sleep time, user agents, cookies, and external-URL policy.

## Provenance labels

Evidence distilled into this reference includes: `docs/downloads.rst`, `docs/crawls.rst`, `docs/url-management.rst`, `docs/sources.rst`, `docs/tutorial0.rst`, `docs/usage-cli.rst`, `docs/troubleshooting.rst`, `docs/settings.rst`, `trafilatura/downloads.py`, `trafilatura/feeds.py`, `trafilatura/sitemaps.py`, `trafilatura/spider.py`, `trafilatura/cli.py`, `trafilatura/cli_utils.py`, `trafilatura/utils.py`, and discovery/download native tests.
