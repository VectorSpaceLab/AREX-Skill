# Querying CLI reference

## One-shot query

```bash
python -m paperai.query "hypertension treatment" 10 /data/papers 0.25
```

Positional order is `query`, optional integer `topn`, optional model directory,
and optional float `threshold`. The model directory must contain the database
and saved txtai model. The command prints a Rich-formatted query, highlights,
and grouped article metadata/results to stdout.

## Interactive shell

```bash
paperai /data/papers
```

The installed console entry point is `paperai = paperai.shell:main`. It loads the
model and database before entering a `cmd.Cmd` loop, uses the `(paperai)` prompt,
and closes the database on exit. Treat this as an interactive workflow, not a
non-blocking smoke test. To verify installation without hanging, import
`paperai.shell` or inspect the entry point, then test `Query.run` with a fixture.

## API integration

Configure txtai's API to load `paperai.api.API` (the package's public class).
A request such as `/search?query=hypertension&limit=5&threshold=0.25` returns
enriched article dictionaries rather than bare section ids. The API uses the
same SQLite/model directory contract as the CLI.

## Optional Streamlit pattern

The repository's search application constructs `Models.load(path)`, calls
`Query.search`, groups with `Query.documents`, and displays article metadata.
Recreate that pattern in a new application only after installing optional
Streamlit/pandas/HTML-cleaning dependencies; the core package does not require a
browser or server for CLI/API use.
