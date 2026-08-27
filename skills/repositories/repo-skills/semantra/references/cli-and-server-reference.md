# Semantra CLI and Server Reference

## Purpose

Read this for Semantra's top-level command shape, option groups, safe installed
package checks, and the local server routes shared across sub-skills.

## Entry point

Semantra installs a console command:

```sh
semantra [OPTIONS] [FILENAME]...
```

The positional filenames must be existing files unless the command exits early
with a flag such as `--help`, `--version`, `--list-models`, or
`--show-semantra-dir`.

Safe checks:

```sh
semantra --help
semantra --version
semantra --list-models
semantra --show-semantra-dir
```

Use [inspect_semantra_install.py](../scripts/inspect_semantra_install.py) when
you need a richer import/CLI diagnostic that does not start the server or
download models.

## Option groups

### Input, cache, and preprocessing

| Option | Default | Purpose | Owning sub-skill |
| --- | --- | --- | --- |
| `FILENAME...` | required for processing | Text/PDF files to analyze. | [document-indexing](../sub-skills/document-indexing/SKILL.md) |
| `--encoding TEXT` | `utf-8` | Encoding for non-PDF text files. | document-indexing |
| `--windows TEXT` | `128_0_16` | Comma-separated window specs `size[_offset][_rewind]`. | document-indexing |
| `--semantra-dir PATH` | application directory | Cache directory for tokens, configs, embeddings, Annoy, and PDF artifacts. | document-indexing |
| `--show-semantra-dir` | false | Print the default cache directory and exit. | document-indexing |
| `--force` | false | Reprocess even when a matching cache group exists. | document-indexing |
| `--silent` | false | Suppress progress output. | document-indexing |
| `--no-server` | false | Process/cache documents and exit without starting Flask. | document-indexing |

### Model and embedding backend

| Option | Default | Purpose | Owning sub-skill |
| --- | --- | --- | --- |
| `--model [openai|minilm|mpnet|sgpt|sgpt-1.3B]` | `mpnet` | Select a preset embedding model. | [models-and-embeddings](../sub-skills/models-and-embeddings/SKILL.md) |
| `--transformer-model TEXT` | none | Use a custom Hugging Face transformer model instead of a preset. | models-and-embeddings |
| `--pool-size INTEGER` | preset-specific | Max token count per embedding pool. | models-and-embeddings |
| `--pool-count INTEGER` | preset-specific | Max number of embeddings per pool. | models-and-embeddings |
| `--doc-token-pre`, `--doc-token-post` | none | Tokens added around document spans for compatible transformer models. | models-and-embeddings |
| `--query-token-pre`, `--query-token-post` | none | Tokens added around query spans for compatible transformer models. | models-and-embeddings |
| `--no-confirm` | false | Skip OpenAI cost confirmation. | models-and-embeddings |

### Query and ranking behavior

| Option | Default | Purpose | Owning sub-skill |
| --- | --- | --- | --- |
| `--num-results INTEGER` | `10` | Results retrieved per file. | [interactive-search](../sub-skills/interactive-search/SKILL.md) |
| `--annoy` | true | Use Annoy approximate kNN instead of exact exhaustive kNN. | interactive-search |
| `--num-annoy-trees INTEGER` | `100` | Annoy tree count. | document-indexing + interactive-search |
| `--svm` | false | Use a per-query linear SVM ranking path. | models-and-embeddings + interactive-search |
| `--svm-c FLOAT` | `1.0` | SVM regularization parameter. | interactive-search |
| `--explain-split-count` | `9` | Number of split candidates for explanation highlighting. | interactive-search |
| `--explain-split-divide` | `6` | Divisor controlling explanation split length. | interactive-search |
| `--num-explain-highlights` | `2` | Number of explanation highlights returned. | interactive-search |

### Local server

| Option | Default | Purpose | Owning sub-skill |
| --- | --- | --- | --- |
| `--host TEXT` | `127.0.0.1` | Host interface for Flask. `0.0.0.0` exposes beyond localhost. | interactive-search |
| `--port INTEGER` | `8080` | Flask port. Change if occupied. | interactive-search |

## Server routes at a glance

Semantra's Flask app serves the bundled web UI and JSON routes for the current
process's documents.

| Route | Purpose |
| --- | --- |
| `/` and static paths | Serve the bundled Svelte application. |
| `/api/files` | List active files and file types. |
| `/api/text` | Return token chunks for a file. |
| `/api/query` | Main query endpoint; dispatches exact, Annoy, or SVM ranking. |
| `/api/queryann` | Annoy query path. |
| `/api/querysvm` | SVM query path; requires `scikit-learn`. |
| `/api/explain` | Compute highlight spans inside one result. |
| `/api/getfile` | Serve the original file. |
| `/api/pdfpositions` | Return PDF page-position metadata. |
| `/api/pdfpage` | Render one PDF page image. |
| `/api/pdfchars` | Return PDF character boxes for highlighting. |

Read [interactive-search web API reference](../sub-skills/interactive-search/references/web-api-reference.md)
for request and response details.

## Common command patterns

Preprocess only:

```sh
semantra --no-server --semantra-dir ./semantra-cache --model minilm documents/*.txt
```

Index and launch UI:

```sh
semantra --semantra-dir ./semantra-cache report.pdf notes/*.txt
```

Use a custom model:

```sh
semantra --transformer-model intfloat/multilingual-e5-base documents/*.txt
```

Avoid port 8080:

```sh
semantra --port 8081 documents/*.txt
```
