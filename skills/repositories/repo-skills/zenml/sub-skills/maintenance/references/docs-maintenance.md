# Docs Maintenance

ZenML documentation maintenance spans GitBook source docs, SDK docs generated from docstrings, link checking, spelling, and TOC-driven URL behavior.

## Sources of Truth

- Edit GitBook content under `docs/book`.
- Do not edit generated docs output directories; generated SDK docs are built from Python docstrings and docs tooling.
- If user-facing behavior changes, update docs or explicitly state why no docs update is needed.
- Use US English spelling in docs, code comments, docstrings, and UI text.

## GitBook URL and TOC Rules

GitBook URLs do not simply mirror file paths. The table of contents determines public URL nesting.

- When adding a page, update the relevant `toc.md` so the page appears in navigation.
- Child pages inherit URL nesting from their parent entry in `toc.md`.
- Pro docs are served under `/pro/` even though their source files live under the ZenML Pro docs subtree.
- Cross-section links, especially OSS-to-Pro or Pro-to-OSS links, should use absolute `https://docs.zenml.io/...` URLs.
- Relative Markdown links are safest only within the same TOC section.
- Check existing links in the same section before inventing a new URL pattern.

## Local Docs Checks

Choose checks based on the change:

| Change | Suggested check | Notes |
| --- | --- | --- |
| Markdown page edits | `python scripts/check_relative_links.py` | Validates relative Markdown links. |
| Internal docs links | `python scripts/check_broken_links.py` | CI-oriented broken-link checker. |
| Local/image/HTML/external links | `lychee --offline --no-progress 'docs/book/**/*.md'` | Offline mode is faster and avoids bot-blocked external sites. |
| Public URL changes | `lychee --no-progress 'docs/book/**/*.md'` | External checks may produce bot-block false positives governed by config. |
| New docs page | inspect `toc.md` and run link checks | URL path follows TOC hierarchy. |
| Typos or wording | `bash scripts/check-spelling.sh` | Uses project spelling policy; prefer US English. |
| Formatting | `bash scripts/format.sh docs/book <changed docs>` | Mutates files; include scoped paths when possible. |

If `requests`, `lychee`, `ruff`, `yamlfix`, or spelling tools are missing, report the missing dependency and recommend the minimal install rather than running broader setup automatically.

## SDK Docs and Docstrings

SDK docs are generated from docstrings. When changing public Python APIs:

- Update Google-style docstrings where the user-facing contract changed.
- Keep type hints and docstrings consistent with actual signatures.
- Be careful with Pydantic v2 models, FastAPI schemas, and generated API docs because broken docstrings can fail CI.
- Local SDK docs serving is heavier than Markdown checks and can mutate generated files; reserve it for docstring/API docs work that needs rendering validation.

Maintainer-context SDK docs commands include:

```bash
python docs/mkdocstrings_helper.py
mkdocs serve -f docs/mkdocs.yml -a localhost:<PORT>
```

Treat SDK serving as opt-in because it starts a long-running process and may require additional dependencies.

## Link Checker Pitfalls

- GitBook paths may differ from source paths; a local relative link that resolves can still point to the wrong public URL when converted to an absolute docs URL.
- External sites can return `403`, `406`, `429`, or `502` to bots; check whether the link checker config already exempts known bot-hostile domains before changing content.
- The CI Markdown link scripts may not check images, `.gitbook` paths, HTML anchors, or external URLs; use Lychee when those matter.
- Do not replace working internal relative links with absolute public URLs unless cross-section or published URL behavior requires it.

## Docs Change Checklist

- Page content follows nearby tone and structure.
- New pages are added to the correct `toc.md`.
- Moved/renamed pages update inbound links and redirects if required.
- Code examples remain executable or clearly marked as illustrative.
- Screenshots/assets live in the appropriate `.gitbook` folder and are referenced by stable relative paths.
- User-facing source changes include docs or a reason docs are unnecessary.
- Spelling uses US English.

## Cross-Skill Routing

- Use `../pipeline-authoring/SKILL.md` for pipeline, step, materializer, schedule, dynamic pipeline, and local execution examples.
- Use `../cli-and-client/SKILL.md` for CLI command and Client API examples.
- Use `../stacks-and-integrations/SKILL.md` for stack component, integration, service connector, orchestrator, and optional dependency examples.
- Return here for docs formatting, link checking, TOC placement, spelling, and PR-readiness notes.
