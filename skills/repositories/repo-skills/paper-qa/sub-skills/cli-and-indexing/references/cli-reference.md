# PaperQA `pqa` CLI Reference

This reference is distilled for runtime use. It is self-contained and does not
require reopening project source files.

## Command shape

The installed command is `pqa`. The runtime parser exposes this shape:

```bash
pqa [GLOBAL_SETTINGS_FLAGS...] {view,save,ask,search,index} [COMMAND_ARGS...]
```

Global flags include:

- `--settings NAME` / `-s NAME`: select a named settings JSON. PaperQA looks for
  a user-saved settings file first, then bundled settings.
- `--index NAME` / `-i NAME`: select the search index name for `search` or
  `index`. In the inspected CLI implementation, `ask` ignores this argparse
  value; use `--agent.index.name NAME` or a saved settings file to make `ask`
  use a named index. The default value is the sentinel `default`; see
  [indexing-workflows.md](indexing-workflows.md) for precedence details.
- Top-level settings flags such as `--llm`, `--summary_llm`, `--embedding`,
  `--temperature`, `--batch_size`, `--verbosity`.
- Nested settings flags using dotted names, for example
  `--agent.index.paper_directory`, `--agent.index.index_directory`,
  `--agent.index.manifest_file`, `--agent.index.recurse_subdirectories`,
  `--agent.index.sync_with_paper_directory`, and
  `--agent.index.use_absolute_paper_directory`.

Prefer putting settings flags before the subcommand. Use `true` / `false` for
boolean settings and quote JSON/dict-valued settings.

## Subcommands

### `pqa view`

Prints the selected `Settings` JSON after applying CLI overrides. It is the
safest first check because it does not ask a question or build an index.

```bash
pqa --settings fast \
  --agent.index.paper_directory "$HOME/Documents/papers" \
  --agent.index.recurse_subdirectories true \
  view
```

Use this to confirm that `paper_directory`, `index_directory`, models, and
boolean flags parse as intended.

### `pqa save LOCATION`

Saves the selected settings after CLI overrides.

```bash
pqa --settings high_quality \
  --temperature 0.2 \
  --agent.index.paper_directory "$HOME/Documents/papers" \
  save my-paper-settings
```

Important semantics:

- `--settings` selects the base settings to load; it is not the destination.
- `LOCATION` is the destination. A relative name is saved as a JSON settings
  file under PaperQA's settings state directory. If the name lacks `.json`,
  PaperQA appends it.
- An absolute `LOCATION` writes exactly there.
- To inspect the saved file through PaperQA, run `pqa --settings my-paper-settings view`.

### `pqa index DIRECTORY`

Builds or updates a local full-text index from a user document directory. This
command may parse files, embed text chunks, and call metadata/LLM providers
unless settings avoid those providers.

```bash
pqa --settings fast \
  --index my-papers \
  --agent.index.paper_directory "$HOME/Documents/papers" \
  --agent.index.index_directory "$HOME/.cache/paperqa-indexes" \
  --agent.index.manifest_file manifest.csv \
  --agent.index.recurse_subdirectories true \
  index "$HOME/Documents/papers"
```

Notes:

- The `DIRECTORY` positional argument is required by the installed parser.
- `--index my-papers` gives the index a stable name.
- `--agent.index.paper_directory` should match the directory being indexed when
  the same settings will later be reused for `ask`.
- Use a manifest CSV when DOI/title metadata should be deterministic.

### `pqa search QUERY`

Runs full-text search against an existing PaperQA search index and prints any
matching saved objects. Searching an existing index does not itself generate an
answer, but it depends on an index that was previously built by `pqa index` or
`pqa ask`.

```bash
pqa --index my-papers \
  --agent.index.index_directory "$HOME/.cache/paperqa-indexes" \
  search "thermoelectric nanostructure"
```

To search previous generated answers, use the special answer index name:

```bash
pqa --index answers \
  --agent.index.index_directory "$HOME/.cache/paperqa-indexes" \
  search "ranking and contextual summarization"
```

The answer index is populated by successful `pqa ask` / agent runs and is stored
under the same `index_directory` as other indexes.

### `pqa ask QUERY`

Runs PaperQA's CLI RAG workflow for a question. With the default tool set this
can build/update the local paper index first, then use LLMs, embeddings, and
metadata providers to retrieve evidence and generate a cited answer. It also
stores the answer in the `answers` index.

```bash
pqa --settings fast \
  --agent.index.name my-papers \
  --agent.index.paper_directory "$HOME/Documents/papers" \
  --agent.index.index_directory "$HOME/.cache/paperqa-indexes" \
  ask "Which papers discuss oxide thermoelectrics?"
```

Before running `ask`, verify that provider credentials, local model servers, or
other configured services are available. If the user only wants a dry run, use
`pqa view`, `pqa search`, or `scripts/inspect_cli.py` instead.

## Settings flags that matter most for CLI indexing

- `--agent.index.paper_directory PATH`: source folder scanned for documents.
- `--agent.index.index_directory PATH`: directory that stores all named,
  autogenerated, and answer indexes.
- `--agent.index.manifest_file PATH_OR_NAME`: CSV manifest path; relative paths
  are resolved from `paper_directory` if not found directly.
- `--agent.index.name NAME`: named index embedded in settings. When `--index` is
  left at `default`, this settings value takes precedence over an autogenerated
  name for `index`/`search`; it is also the reliable way to select a named index
  for `ask`.
- `--agent.index.use_absolute_paper_directory true|false`: when true, indexed
  file locations become user-specific absolute paths. Keep false for shareable
  indexes unless there is a specific reason.
- `--agent.index.recurse_subdirectories true|false`: recursive source scan is
  true by default.
- `--agent.index.concurrency N`: concurrent file reads / index additions. Lower
  it for rate limits or fragile services.
- `--agent.index.batch_size N`: number of files processed before committing.
- `--agent.index.sync_with_paper_directory true|false`: true updates/removes
  index entries to match the source directory; false is useful for read-only
  reuse diagnostics of an already-built index.
- `--agent.rebuild_index true|false`: CLI agent runs normally rebuild/sync the
  index before searching. Set false only when an existing non-empty index should
  be loaded as-is.

For provider and model tuning, defer to the settings/configuration sub-skill.
