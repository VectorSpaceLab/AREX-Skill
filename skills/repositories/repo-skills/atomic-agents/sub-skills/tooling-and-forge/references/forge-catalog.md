# Atomic Forge Catalog

Atomic Forge is a collection of downloadable tools that users copy into their own projects. The skill should describe them as installable tool packages, not as framework-internal dependencies.

| Tool | What it does | Common dependencies / needs | Safety note |
| --- | --- | --- | --- |
| `calculator` | symbolic arithmetic through SymPy | `sympy` only | safe local math helper |
| `datetime_tool` | now / parse / convert / shift / diff | `tzdata` / `zoneinfo`-friendly timezone data | safe local date-time helper |
| `arxiv_search` | search arXiv papers | network, public API | safe but network-backed |
| `bocha_search` | BoCha web search | network and service credentials if required by deployment | search service integration |
| `hackernews_search` | search HN stories/comments | network, Algolia API | safe public search |
| `pdf_reader` | read local or remote PDFs | `pypdf`, `requests` | local/remote document extraction |
| `searxng_search` | query a SearXNG instance | network and a SearXNG endpoint | self-hosted search integration |
| `tavily_search` | Tavily search | Tavily API key / network | key-backed search |
| `weather` | current conditions and forecast | Open-Meteo / no key | safe public weather API |
| `webpage_scraper` | scrape and convert webpages to markdown | `requests`, `beautifulsoup4`, `markdownify`, `readability-lxml`, `lxml` | network-backed scraping |
| `wikipedia_search` | search Wikipedia in any language | network, public API | safe public search |
| `youtube_transcript_scraper` | fetch YouTube transcripts | network, YouTube transcript API | safe if URL is public |
| `fia_signals` | crypto market intelligence | network / service data | finance-oriented, may be rate-limited |

## Tool-packaging pattern

Each downloadable tool package generally includes:

- `README.md` with purpose, usage, and env vars
- `pyproject.toml`
- `requirements.txt`
- `.coveragerc`
- `tool/` with the actual implementation
- `tests/` with focused unit tests

## When to read this file

Read this file when the user asks which Atomic Forge tool family fits the task, what dependency or credential a tool needs, or how to explain a downloaded tool package without reopening the original repo.
