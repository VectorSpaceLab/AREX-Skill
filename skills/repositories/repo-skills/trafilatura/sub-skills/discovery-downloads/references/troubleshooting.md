# Discovery and Download Troubleshooting

Use this matrix when discovery returns too few URLs, downloads return `None`, queues appear stalled, or crawling behaves unexpectedly. Separate discovery, network retrieval, and extraction problems before changing settings.

## Fast triage

1. **Does the URL validate?** Try a simpler homepage URL and confirm the scheme is `http://` or `https://`.
2. **Do you need decoded HTML or response diagnostics?** Switch from `fetch_url()` to `fetch_response(decode=True, with_headers=True)` to inspect status, final URL, body length, and headers.
3. **Is `fetch_url()` rejecting a downloaded response?** It returns `None` for failed requests, non-200 statuses, or unacceptable size constraints. `fetch_response()` can reveal which case it is.
4. **Are you discovering or downloading?** Use `--list` with `--feed`/`--sitemap` first. Review URLs before extracting pages.
5. **Are you overloading one domain?** Increase `SLEEP_TIME`/`sleep_time`, lower `--parallel`, and rely on `UrlStore` domain backoff.
6. **Is the page unavailable now?** Try `--archived`, an Internet Archive URL, or predownloaded HTML.

## Download result is `None`

| Symptom | Likely cause | Checks | Actions |
| --- | --- | --- | --- |
| `fetch_url(url)` returns `None`; `fetch_response()` also returns `None` | Network failure, timeout, invalid URL, DNS/TLS/proxy problem | `response = fetch_response(url, decode=True, with_headers=True)`; check whether it is `None` | Validate URL, retry later, set proxy correctly, lower concurrency, increase `DOWNLOAD_TIMEOUT`, or predownload externally. |
| `fetch_response()` returns status not 200 | Server rejects, redirects exhausted, auth required, rate limit, not found | Inspect `response.status`, `response.url`, headers | Respect server policy; retry later; add cookies/user-agent via config if authorized; use archive fallback for link rot. |
| `fetch_response()` has data but `fetch_url()` returns `None` | `fetch_url()` applies status and size/suitability checks | Inspect `len(response.data)`, `response.status`, active `MIN_OUTPUT_SIZE`/`MAX_FILE_SIZE` | If the page is valid for your task, handle `Response` directly or adjust config carefully. |
| Error mentions file size or stream aborted | `MAX_FILE_SIZE` exceeded | Check config `MAX_FILE_SIZE` and body length | Raise `MAX_FILE_SIZE` only if large HTML is expected; otherwise skip oversized files. |
| Page downloads but extraction later finds nothing | This is no longer a download issue | Save/inspect HTML; route to extraction/output troubleshooting | Consider JavaScript rendering/predownloaded HTML or extraction recall options in the extraction sub-skill. |

## SSL and certificate failures

Trafilatura supports `no_ssl=True` for direct API calls:

```python
from trafilatura.downloads import fetch_response

response = fetch_response("https://example.org/", decode=True, no_ssl=True)
```

Notes:

- The urllib3 backend retries SSL errors once with certificate verification disabled. The pycurl backend also retries known SSL error classes with verification disabled.
- `no_ssl=True` weakens transport verification. Use it for controlled diagnostics or known broken certificate chains, not as a default.
- If a corporate proxy re-signs TLS, configure the environment/proxy/certificates instead of blindly disabling verification.

## Proxy and SOCKS routing

Trafilatura reads `http_proxy` when the downloads module is loaded. With the optional SOCKS support from `urllib3[socks]`, URLs like these can route requests through a SOCKS proxy:

```bash
export http_proxy=socks5://PROXYHOST:PROXYPORT
export http_proxy=socks5://USER:PASSWORD@PROXYHOST:PROXYPORT
python my_download_script.py
```

Troubleshooting actions:

- Set `http_proxy` before importing `trafilatura.downloads` or starting the `trafilatura` CLI process.
- If setting the proxy inside an already-running Python process, assign `trafilatura.downloads.PROXY_URL` manually and reset/recreate pools if necessary.
- Install optional `urllib3[socks]` support for SOCKS proxy URLs.
- Optional `pycurl` also honors Trafilatura's proxy setting through its curl handle.
- Keep proxy credentials out of committed scripts, runtime skill files, and logs.

## Blocked requests, rate limits, and user-agent issues

| Sign | Interpretation | Response |
| --- | --- | --- |
| HTTP 403/429/503 or repeated timeouts from one host | IP/user-agent/rate limiting or server overload | Reduce concurrency, increase `SLEEP_TIME`, retry later, and respect robots/policies. |
| Works in a browser but not with Trafilatura | User-agent/cookies/JavaScript/auth differences | If authorized, set `USER_AGENTS` and `COOKIE` in config; otherwise predownload with a compliant browser automation workflow and pass files to Trafilatura. |
| Only some domains fail in a batch | Domain-specific blocking or certificate/proxy differences | Track failures per domain; do not treat global package installation as the cause. |
| Server blocks Trafilatura user-agent | The default user-agent may be denied | Use an allowed custom user-agent only when you have permission and identify your crawler honestly. |

Trafilatura's downloader and crawler do not bypass access controls, paywalls, anti-bot systems, or robots restrictions. They provide polite retrieval and diagnostics.

## Timeouts, redirects, and retries

Relevant config keys:

```ini
[DEFAULT]
DOWNLOAD_TIMEOUT = 30
MAX_REDIRECTS = 2
SLEEP_TIME = 5
MAX_FILE_SIZE = 20000000
```

Actions:

- Increase `DOWNLOAD_TIMEOUT` for slow sites, but do not use a huge timeout in broad queues.
- Check `response.url` to see the final URL after redirects.
- If redirect loops or login redirects occur, skip or handle outside Trafilatura.
- Status codes such as 429, 500, 502, 503, 504, and related transient server/proxy codes are retry candidates in the urllib3 strategy, bounded by `MAX_REDIRECTS`/retry settings.

## Queue appears stalled or too slow

| Symptom | Cause | Fix |
| --- | --- | --- |
| `load_download_buffer()` sleeps repeatedly | All remaining domains are still in backoff or no eligible URLs remain | Wait, reduce `sleep_time` only in safe tests, or confirm `url_store.done`. |
| Few URLs in each buffer despite many input URLs | Many URLs belong to the same domain; domain-aware throttling is working | Add more domains, increase patience, or intentionally process one domain slowly. |
| Too many requests hit one host | Bypassing `UrlStore` or using unsafe custom loops | Use `add_to_compressed_dict()` + `load_download_buffer()`; avoid raw `ThreadPoolExecutor(fetch_url)` on one domain. |
| URL list contains duplicates/noise | Input not cleaned | Use `add_to_compressed_dict()`, `--url-filter`, `--blacklist`, and optional courlan filtering before downloads. |

## Robots, crawl delay, and politeness

Focused crawling honors robots rules when they can be fetched and parsed.

```python
from trafilatura.spider import parse_robots

rules = parse_robots("https://example.org/robots.txt", "User-agent: *\nDisallow: /private\nCrawl-delay: 10")
assert rules.can_fetch("*", "https://example.org/public")
assert not rules.can_fetch("*", "https://example.org/private")
```

Guidance:

- Use the focused crawler for intra-site discovery; do not convert it into an unbounded broad crawler.
- Respect `Crawl-delay` where present. Trafilatura stores crawl-delay metadata in the URL store and uses it for crawler sleeps.
- When robots cannot be fetched, use conservative defaults and avoid sensitive paths.
- Starting a crawl from a subpath narrows the reference path. This is useful for section crawls but can make output look unexpectedly small.

## Feed discovery returns no links

| Cause | Check | Action |
| --- | --- | --- |
| Input URL is invalid or cannot be downloaded | `find_feed_urls("http://")`-like inputs return empty | Validate and try the homepage. |
| Homepage has no feed discovery tags or feed-like anchors | Use lower-level `determine_feed(homepage_html, params)` on predownloaded HTML | Try sitemap discovery or focused crawling. |
| Feed exists but is a comments feed | Comment feeds are intentionally rejected | Use a section/article feed instead. |
| Feed item links are external and `external=False` | Similar-domain filter rejects divergent domains | Use `external=True` only when external item URLs are expected. |
| Language/path filter is too narrow | Test without `target_lang` or `--url-filter` | Relax filters, then reapply manually. |
| JSON feed malformed | `extract_links()` returns empty | Validate or pre-clean the feed body. |

Offline parsing check:

```python
from trafilatura.feeds import FeedParameters, extract_links
params = FeedParameters("https://example.org", "example.org", "")
print(extract_links('<?xml version="1.0"?><rss><channel><link>https://example.org/a</link></channel></rss>', params))
```

## Sitemap discovery returns no links

| Cause | Check | Action |
| --- | --- | --- |
| Base URL not live | `sitemap_search()` checks the base before proceeding | Try a reachable base, direct sitemap URL, archive, or predownloaded sitemap body. |
| robots.txt is missing or has no sitemap entries | `extract_robots_sitemaps()` on robots body | Let Trafilatura try guesses, or provide the known sitemap URL. |
| Sitemap body is HTML/error page | `is_plausible_sitemap()` rejects HTML-like sitemap responses | Inspect the URL; skip, retry later, or use the correct sitemap. |
| `max_sitemaps` too low | Nested sitemap index stops early | Raise `max_sitemaps` within budget. |
| Language/path/external filters too strict | Test without `target_lang`, subpage input, or `--url-filter` | Relax filters or parse predownloaded sitemap manually. |
| Gzipped sitemap decoding unavailable or failed | Body appears binary or empty | Ensure compressed decoding dependencies where needed; predownload/decompress externally if necessary. |

## Focused crawler returns too few links

| Cause | Check | Action |
| --- | --- | --- |
| Start URL has no internal links | Try homepage instead of an article page | Seed with a section/homepage or use sitemap/feed discovery first. |
| Reference path too narrow | Starting at `/section/` keeps links containing that reference | Start from the site root or desired broader section. |
| Robots rules disallow paths | Inspect `rules.can_fetch("*", url)` | Respect robots; choose allowed sections. |
| Optional language gate filters out content | Compare with `lang=None` | Use `lang` only when language-specific crawling is needed. |
| Global crawler state leaked from previous crawl | `spider.URL_STORE` contains old URLs | Reset `spider.URL_STORE = UrlStore(compressed=False, strict=False)` between unrelated crawls. |
| `max_seen_urls` or `max_known_urls` is too small | Check returned `to_visit` and `known_links` sizes | Increase limits gradually. |

## `--archived` and link rot

`--archived` is for URL-processing pipelines after direct download failures. It retries failed URLs through the Internet Archive URL prefix.

```bash
trafilatura -i urls.txt -o extracted/ --archived
```

Use it when:

- Pages are gone, intermittently unavailable, or domains expired.
- You only need the archived representation and accept possible timestamp/content drift.

Do not use it when:

- You require the current live page.
- The archive snapshot is blocked, missing, or legally inappropriate for your task.

Python equivalent:

```python
from trafilatura.downloads import fetch_url

html = fetch_url(url)
if html is None:
    html = fetch_url("https://web.archive.org/web/20/" + url)
```

## Optional extras and when they matter

| Extra/dependency | Helps with | Install path |
| --- | --- | --- |
| `pycurl` | Alternative download backend; may behave differently from urllib3 on some sites. | Install directly or via `trafilatura[all]`. |
| `urllib3[socks]` | SOCKS proxy support for urllib3 manager. | Install urllib3 SOCKS extra or `trafilatura[all]` when available. |
| `brotli` | Decode Brotli-compressed responses. | Included by `trafilatura[all]`. |
| `zstandard` | Decode Zstandard-compressed responses and advertise `zstd` support. | Included by `trafilatura[all]`. |
| `py3langid` | Content language detection in focused crawling and probing. | Included by `trafilatura[all]`. |
| `faust-cchardet` / htmldate speed extras | Faster encoding/date-related paths in larger workflows. | Included by `trafilatura[all]` or relevant dependency extras. |

Only install broad extras when the task requires them. Base download/feed/sitemap/crawl APIs work without all optional extras, but behavior around proxies, compression, language checks, and backend-specific failures can differ.

## Local/offline validation failures

Run:

```bash
python skills/disco/trafilatura/sub-skills/discovery-downloads/scripts/discovery_smoke.py
```

Interpretation:

- Import/signature assertion fails: installed Trafilatura version or API has drifted.
- Offline feed/sitemap assertion fails: parser behavior changed; update workflows and tests before trusting discovery guidance.
- Mocked crawler assertion fails: focused-crawler state or `Response` handling changed; verify crawler section before use.
- Any live-network activity during the smoke is a bug in the smoke script; it should use only inline fixtures and mocks.

## Source evidence labels

Troubleshooting guidance is based on behavior evidenced by the download, feed, sitemap, spider, CLI, settings, URL-management, source-discovery, tutorial, and troubleshooting documentation/source/test surfaces. These labels are provenance only; this reference is intended to be sufficient without reopening the repository.
