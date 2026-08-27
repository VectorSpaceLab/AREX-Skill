#!/usr/bin/env python3
"""Offline smoke checks for the Trafilatura discovery-downloads sub-skill.

The script intentionally avoids live network access. It uses inline fixtures and
mocked fetch functions to verify imports, signatures, response objects, queue
helpers, feed parsing, sitemap parsing, CLI argument mapping, and one focused
crawler state transition.
"""

from __future__ import annotations

import inspect
from unittest.mock import patch

from courlan import UrlStore

import trafilatura.downloads as downloads
import trafilatura.feeds as feeds
import trafilatura.sitemaps as sitemaps
from trafilatura import spider
from trafilatura.cli import parse_args
from trafilatura.utils import Response


def _assert_signature(fn, required: list[str]) -> None:
    params = inspect.signature(fn).parameters
    missing = [name for name in required if name not in params]
    assert not missing, f"{fn.__name__} missing parameters: {missing}; saw {list(params)}"


def check_signatures() -> None:
    _assert_signature(downloads.fetch_url, ["url", "no_ssl", "config", "options"])
    _assert_signature(downloads.fetch_response, ["url", "decode", "no_ssl", "with_headers", "config"])
    _assert_signature(
        downloads.add_to_compressed_dict,
        ["inputlist", "blacklist", "url_filter", "url_store", "compression", "verbose"],
    )
    _assert_signature(downloads.load_download_buffer, ["url_store", "sleep_time"])
    _assert_signature(downloads.buffered_downloads, ["bufferlist", "download_threads", "options"])
    _assert_signature(feeds.find_feed_urls, ["url", "target_lang", "external", "sleep_time"])
    _assert_signature(sitemaps.sitemap_search, ["url", "target_lang", "external", "sleep_time", "max_sitemaps"])
    _assert_signature(
        spider.focused_crawler,
        ["homepage", "max_seen_urls", "max_known_urls", "todo", "known_links", "lang", "config", "rules", "prune_xpath"],
    )


def check_response_object() -> None:
    body = b"<html><body><p>ok</p></body></html>"
    response = Response(body, 200, "https://example.org/final")
    assert response.data == body
    assert response.status == 200
    assert response.url.endswith("/final")
    response.store_headers({"Content-Type": "text/html", "X-Test": "yes"})
    assert response.headers == {"content-type": "text/html", "x-test": "yes"}
    response.decode_data(True)
    assert response.html == body.decode("utf-8")
    assert response.as_dict()["status"] == 200


def check_url_store_and_buffered_downloads() -> None:
    urls = [
        "https://example.org/news/a",
        "https://example.org/private",
        "https://example.net/news/b",
        "https://example.com/blog/c",
    ]
    store = downloads.add_to_compressed_dict(
        urls,
        blacklist={"example.org/private"},
        url_filter=["/news", "/blog"],
    )
    dumped = store.dump_urls()
    assert "https://example.org/private" not in dumped
    assert "https://example.org/news/a" in dumped
    assert "https://example.net/news/b" in dumped

    bufferlist, store = downloads.load_download_buffer(store, sleep_time=0.0)
    assert bufferlist, "expected at least one eligible buffered URL"
    assert all(url.startswith("https://example.") for url in bufferlist)

    with patch.object(downloads, "fetch_url", side_effect=lambda url, options=None: f"<html>{url}</html>"):
        results = dict(downloads.buffered_downloads(bufferlist, download_threads=2))
    assert set(results) == set(bufferlist)
    assert all(value.startswith("<html>https://") for value in results.values())

    assert list(downloads.buffered_response_downloads([], 1)) == []


def check_feeds_offline() -> None:
    params = feeds.FeedParameters("https://example.org", "example.org", "https://example.org/")

    homepage = '<html><head><link rel="alternate" type="application/rss+xml" href="/feed.xml"></head></html>'
    feed_urls = feeds.determine_feed(homepage, params)
    assert feed_urls == ["https://example.org/feed.xml"]

    rss = '<?xml version="1.0"?><rss><channel><link>https://example.org/news/item-1</link></channel></rss>'
    assert feeds.extract_links(rss, params) == ["https://example.org/news/item-1"]

    json_feed = '{"version":"https://jsonfeed.org/version/1","items":[{"id":"https://example.org/news/json-1"}]}'
    assert feeds.extract_links(json_feed, params) == ["https://example.org/news/json-1"]

    def fake_fetch(url: str):
        if url == "https://example.org/":
            return homepage
        if url == "https://example.org/feed.xml":
            return rss
        raise AssertionError(f"unexpected network URL in feed smoke: {url}")

    with patch.object(feeds, "fetch_url", side_effect=fake_fetch):
        discovered = feeds.find_feed_urls("https://example.org/")
    assert discovered == ["https://example.org/news/item-1"]


def check_sitemaps_offline() -> None:
    robots = "# example\nSitemap: https://example.org/sitemap.xml\n"
    assert sitemaps.extract_robots_sitemaps(robots, "https://example.org") == ["https://example.org/sitemap.xml"]

    xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <urlset>
      <url><loc>https://example.org/en/page-1</loc></url>
      <url><loc>https://example.org/en/page-2</loc></url>
    </urlset>'''
    sitemap = sitemaps.SitemapObject("https://example.org", "example.org", [], target_lang="en")
    sitemap.current_url = "https://example.org/sitemap.xml"
    sitemap.content = xml
    sitemap.process()
    assert sitemap.urls == ["https://example.org/en/page-1", "https://example.org/en/page-2"]

    def fake_fetch(url: str):
        if url == "https://example.org/robots.txt":
            return robots
        if url == "https://example.org/sitemap.xml":
            return xml
        raise AssertionError(f"unexpected network URL in sitemap smoke: {url}")

    with patch.object(sitemaps, "is_live_page", return_value=True), patch.object(sitemaps, "fetch_url", side_effect=fake_fetch):
        discovered = sitemaps.sitemap_search("https://example.org/", target_lang="en", sleep_time=0.0, max_sitemaps=5)
    assert discovered == ["https://example.org/en/page-1", "https://example.org/en/page-2"]


def check_focused_crawler_offline() -> None:
    spider.URL_STORE = UrlStore(compressed=False, strict=False)
    rules = spider.parse_robots("https://example.org/robots.txt", "User-agent: *\nAllow: /\nCrawl-delay: 0")
    assert rules is not None

    page = b'<html><body><a href="https://example.org/section/page-2">next</a></body></html>'

    def fake_fetch_response(url: str, *, decode=False, no_ssl=False, with_headers=False, config=None):
        assert url == "https://example.org/start", f"unexpected crawler URL: {url}"
        response = Response(page, 200, url)
        response.decode_data(decode)
        return response

    with patch.object(spider, "fetch_response", side_effect=fake_fetch_response):
        to_visit, known_links = spider.focused_crawler(
            "https://example.org/",
            max_seen_urls=1,
            max_known_urls=10,
            todo=["https://example.org/start"],
            known_links=[],
            rules=rules,
        )

    assert "https://example.org/start" in known_links
    assert "https://example.org/section/page-2" in known_links
    assert "https://example.org/section/page-2" in to_visit
    assert spider.is_still_navigation(to_visit) is False


def check_cli_navigation_args() -> None:
    args = parse_args(["--sitemap", "https://example.org/", "--list", "--target-language", "en", "--url-filter", "/news"])
    assert args.sitemap == "https://example.org/"
    assert args.list is True
    assert args.target_language == "en"
    assert args.url_filter == ["/news"]

    args = parse_args(["--feed", "https://example.org/feed.xml", "--list"])
    assert args.feed == "https://example.org/feed.xml"

    args = parse_args(["--crawl", "https://example.org/"])
    assert args.crawl == "https://example.org/"


def main() -> None:
    check_signatures()
    check_response_object()
    check_url_store_and_buffered_downloads()
    check_feeds_offline()
    check_sitemaps_offline()
    check_focused_crawler_offline()
    check_cli_navigation_args()
    print("OK discovery_smoke")


if __name__ == "__main__":
    main()
