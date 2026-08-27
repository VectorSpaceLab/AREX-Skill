# API Reference

This page collects the public Python surface that the skill routes most often.
It is intentionally short and practical; deeper workflow guidance lives in the
sub-skill references.

## Core framework

| Object | Signature | Purpose |
| --- | --- | --- |
| `src.common.analysis.Analysis` | `__init__(name: str, description: str)` | Base class for all analysis workflows. Subclasses implement `run()` and may use `progress()`. |
| `src.common.analysis.Analysis.save` | `save(output_dir, formats=None, dpi=300) -> dict[str, Path]` | Runs an analysis and writes figure/data/chart outputs. |
| `src.common.analysis.Analysis.load` | `load(analysis_dir='src/analysis') -> list[type[Analysis]]` | Discovers analysis subclasses by scanning a source tree. |
| `src.common.analysis.AnalysisOutput` | dataclass with `figure`, `data`, `chart`, `metadata` | The return object for analysis workflows. |
| `src.common.indexer.Indexer` | `__init__(name: str, description: str)` | Base class for data-ingestion workflows. Subclasses implement `run()`. |
| `src.common.indexer.Indexer.load` | `load(indexer_dir='src/indexers') -> list[type[Indexer]]` | Discovers indexer subclasses by scanning a source tree. |
| `src.common.client.HttpClient` | `__init__(rate_limit=10, max_retries=5, timeout=30.0, max_connections=20, base_url='')` | Shared HTTP client with retry and throttling behavior. |
| `src.common.storage.ParquetStorage` | `__init__(data_dir='data')` | Chunked Parquet storage for Kalshi market backfills. |

## Chart helpers

| Object | Signature | Notes |
| --- | --- | --- |
| `ChartConfig.to_dict()` | `() -> dict[str, Any]` | Serializes chart config to a dict without `None` fields. |
| `ChartConfig.to_json()` | `() -> str` | JSON export used by `Analysis.save()`. |
| `line_chart()` | `data, x='x', y='y', **kwargs` | Helper for line charts. |
| `bar_chart()` | `data, x='x', y='y', stacked=False, **kwargs` | Helper for bar and stacked-bar charts. |
| `area_chart()` | `data, x='x', y='y', stacked=False, **kwargs` | Helper for area charts. |
| `pie_chart()` | `data, name='name', value='value', **kwargs` | Helper for pie charts. |
| `scatter_chart()` | `data, x='x', y='y', z=None, series=None, **kwargs` | Helper for scatter charts. |
| `heatmap()` | `data, x='x', y='y', value='value', **kwargs` | Helper for heatmaps. |
| `treemap()` | `data, name='name', value='value', children='children', **kwargs` | Helper for treemaps. |

## Domain-specific helpers

| Object | Signature | Notes |
| --- | --- | --- |
| `src.common.util.package.package_data` | `package_data(data_dir=Path('data'), output_path=Path('data.tar.zst')) -> bool` | Creates the dataset archive. The code does not remove `data/`. |
| `src.common.util.strings.snake_to_title` | `snake_to_title(s: str) -> str` | Used by the interactive CLI menus. |
| `src.analysis.kalshi.util.categories.get_hierarchy` | `get_hierarchy(category: str) -> tuple[str, str, str]` | Maps a Kalshi category code to `(group, category, subcategory)`. |
| `src.analysis.kalshi.util.categories.get_group` | `get_group(category: str) -> str` | Backwards-compatible group lookup. |
| `src.analysis.kalshi.util.categories.CATEGORY_SQL` | SQL expression string | Extracts the category prefix from `event_ticker`. |

## API clients

### Kalshi

| Method | Signature | Notes |
| --- | --- | --- |
| `KalshiClient.__init__` | `host='https://api.elections.kalshi.com/trade-api/v2'` | Uses the shared `HttpClient`. |
| `get_market()` | `ticker: str -> Market` | Fetch one market by ticker. |
| `get_market_trades()` | `ticker, limit=1000, verbose=True, min_ts=None, max_ts=None` | Paginates until the API cursor is exhausted. |
| `list_markets()` | `limit=20, **kwargs` | One-page market listing. |
| `iter_markets()` | `limit=200, cursor=None, min_close_ts=None, max_close_ts=None` | Generator that yields `(markets, cursor)` pairs. |
| `get_recent_trades()` | `limit=100` | Convenience trade fetcher. |

### Polymarket

| Method | Signature | Notes |
| --- | --- | --- |
| `PolymarketClient.__init__` | `gamma_url='https://gamma-api.polymarket.com'` | Uses the shared `HttpClient`. |
| `get_markets()` | `limit=500, offset=0, **kwargs` | Accepts either a list response or a `{markets: ...}` response. |
| `iter_markets()` | `limit=500, offset=0` | Generator that yields `(markets, next_offset)` pairs. |

### Polygon blockchain

| Method | Signature | Notes |
| --- | --- | --- |
| `PolygonClient.__init__` | `rpc_url: Optional[str] = None` | Reads `POLYGON_RPC` when no explicit URL is supplied. |
| `get_block_number()` | `() -> int` | Current chain head. |
| `get_block_timestamp()` | `block_number: int -> int` | Block timestamp lookup. |
| `get_trades()` | `from_block, to_block, contract_address=CTF_EXCHANGE` | Decodes `OrderFilled` logs. |
| `iter_trades()` | `from_block, to_block=None, chunk_size=1000, contract_address=CTF_EXCHANGE, max_workers=5` | Chunked and parallel trade fetcher. |
| `get_deployment_block()` | `() -> int` | Returns the approximate Polymarket deployment block. |

## Analysis and indexer discovery caveat

`Analysis.load()` and `Indexer.load()` scan relative paths by default. In a
fresh shell outside the repo root, pass explicit absolute roots instead of
assuming discovery will find the source tree.
