# Data Acquisition Boundaries

## Built-In Acquisition Surfaces

LaTeX-OCR includes utilities for:

- recursively scraping Wikipedia, Math StackExchange, or Physics StackExchange
  pages for math snippets;
- downloading and reading arXiv source bundles;
- reading local `.tex` files or `.tar.gz` source bundles;
- Colab-style downloads of public dataset archives in the training notebook.

## Safety Policy

Do not start scraping, arXiv downloads, or Google Drive downloads without
explicit user approval. These workflows can consume network, trigger rate
limits, download large archives, or process untrusted TeX input. Prefer local
files first.

## Recommended Flow

1. Start from a known local TeX/text corpus.
2. Extract and deduplicate formulas with the bundled local helper.
3. Inspect a small sample manually for syntax quality and macro expansion.
4. Render a small batch to PNG and validate dimensions.
5. Only then scale to large rendering, tokenizer training, and pickle creation.

## External Dataset Notes

The README references im2latex-100k and public Google Drive formula/image data.
Treat those as optional external sources; document provenance, license, and
size before incorporating them into a new training run.
