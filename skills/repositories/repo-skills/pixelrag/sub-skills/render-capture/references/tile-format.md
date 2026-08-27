# Tile Format

PixelRAG renders each input into a tile directory so later stages can chunk and embed images without reparsing the source document.

## Directory shape

Typical URL or HTML render:

```text
tiles/
  example.png.tiles/
    tiles.json
    tile_0000.jpg
    tile_0001.jpg
```

The index pipeline may use numeric stems so article IDs line up with `articles.json`:

```text
index/tiles/
  0.png.tiles/
    tiles.json
    chunks.json        # created by chunking, or by PDF render
    chunk_0000_00.png
```

## `tiles.json`

Important fields include:

- `tiles`: ordered image file names.
- `source` or legacy `url`: source identity used for incremental rerun safety.
- `article_id`: stamped by the index pipeline so embedders do not guess IDs from directory names.
- `viewport_width`, `page_height`, `tile_height`, `complete`: backend-dependent render metadata.

Do not rewrite `article_id` by hand. The index pipeline deliberately checks source identity and re-renders stale tile directories when source enumeration changes.

## PDF behavior

PDF rendering writes one tile per page and also writes `chunks.json`; the chunker sees that file and skips re-splitting because each PDF page is already treated as a semantic unit. At 200 DPI, a page can be wider than 875 px, so downstream embedding code should rely on the recorded chunk/page metadata rather than assuming web-width tiles.

## Image behavior

Local image inputs are copied or resized into a single-tile directory. Very wide images are capped to reduce embedding memory pressure in the index pipeline.

## Handoff to index-build

Before routing to `../index-build/SKILL.md`, verify:

1. Every selected source has a tile directory.
2. Each tile directory has readable `tiles.json`.
3. Tile files exist and are non-empty.
4. If using the orchestrator, let it write `article_id` and `source` stamps; do not pre-stamp manually unless you are reproducing a test fixture.

Use `pixelrag chunk --shard-dir <tiles-dir>` only after this render format is correct.
