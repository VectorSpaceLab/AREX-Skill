# Optional site preview

Core NLP-progress content maintenance is Markdown-only. A Ruby/Jekyll preview is optional and can be skipped when the user only needs text edits and checker validation.

The site is a GitHub Pages-style project. The local preview depends on Ruby, Bundler, network access to RubyGems, and the `github-pages` gem group declared by the repository's Gemfile. Treat setup failures as preview issues, not as blockers for Markdown-only validation unless the user explicitly requires a rendered preview.

## Fast non-network checks first

From the repository root:

From the generated `nlp-progress` skill root:

```bash
python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py <changed-file-or-directory>
python3 sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py --strict <changed-file-or-directory>
```

From this sub-skill directory, use `python3 scripts/check_nlp_progress_markdown.py ...`.

Also use the editor's Markdown preview if available. This catches most table alignment and link mistakes without Ruby.

## Optional Ruby/Bundler preview

Run only when the user asks for a site preview or when a change touches Jekyll/Liquid rendering.

```bash
ruby --version
bundle --version || gem install bundler
bundle install
bundle exec jekyll serve --host 127.0.0.1 --port 4000
```

Then open `http://127.0.0.1:4000/` in a browser or fetch the changed page path with a local HTTP client.

Notes:

- `bundle install` may need network access and may fail if RubyGems, TLS, native extensions, or the configured Ruby version are unavailable.
- Do not require `bundle install` for ordinary result-row or dataset edits.
- If the local port is occupied, choose another port with `--port 4001`.
- If a preview run is interrupted, stop the server process before retrying.

## Liquid include awareness

The site includes helper templates for rendered tables and simple charts:

- A table include can render rows from include data with `Model`, score columns, `Paper / Source`, and `Code`-like links.
- A chart include renders a simple bar chart from result scores.

Most language/task pages use plain Markdown tables. Do not convert a plain Markdown table to Liquid include data unless the user explicitly requests a rendering refactor.

## Preview handoff

When a preview is attempted, report:

- Ruby and Bundler availability.
- The exact command run.
- Whether gems were already available or network installation was attempted.
- The local URL checked.
- Any non-blocking preview limitation, such as unavailable network, missing native Ruby headers, or a busy port.
