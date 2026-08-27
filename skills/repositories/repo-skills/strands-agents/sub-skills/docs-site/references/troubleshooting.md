# Troubleshooting

Use this table when a docs-site change fails validation, renders incorrectly, or
keeps receiving the same review feedback.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Invalid frontmatter or schema failure | Missing `title` or `description`, unsupported field, bad enum value, or `languages` listing both SDKs | Align with the documented schema. Remove invented fields. Omit `languages` when both SDKs are supported. |
| Language banner appears when it should not | `languages` is set on a feature available in both SDKs | Remove `languages` entirely. Use it only for one-language availability. |
| Snippet include renders a diagnostic line | The `--8<--` path is wrong, the section name is wrong, or the marker pair is missing | Check the snippet path relative to the docs content root. Match `[start:name]` and `[end:name]` exactly and keep markers on their own lines. |
| TypeScript snippet typecheck fails | Body snippets redeclare identifiers, imports are missing from the rendered block, or setup lives outside the included region | Put imports in `*_imports.ts`, include imports and body in one fence, and wrap repeated bodies in scoped functions. |
| Tabs do not render or sync correctly | The page used `TabItem`, imported the wrong component, or started a tab with a blank line | Use auto-imported `Tabs` and `Tab`. Remove `TabItem`. Keep tab content tight and label sets consistent. |
| Shared prose is awkward or names both languages | Language-specific identifiers were spelled out manually | Replace the phrase with `<Syntax py="..." ts="..." />` or move language-specific prose inside tabs. |
| Line length drift | Docs prose or snippet template literal contents exceed the site limit | Wrap to 90 characters under the docs content tree. Prettier does not catch every long line. |
| Relative link resolves to a wrong or missing page | Directory depth changed, a file moved, or the link points at a generated API page with a raw relative path | Update the relative file path. Use `@api/python/...` or `@api/typescript/...` for API docs. Preserve anchors. |
| Stale or missing `sourceLinks` | A source file moved, a docs page was copied, or a new implementation-backed page omitted source metadata | Update every affected `sourceLinks` entry in the same change as the move. Add explicit `language` only when extension inference cannot work. |
| Generated API docs look editable but changes vanish | The page is under an `_generated` symlink into generated output | Do not edit generated API docs. Fix source or generator logic, then run `scripts/generate-api-docs.sh`. |
| Generated API pages miss headings or sidebar entries | API docs were not regenerated, TypeDoc or pydoc output changed, or category frontmatter is missing | Regenerate API docs and inspect generated frontmatter. Fix generator output, not the generated page by hand. |
| Sidebar or pagination points outside the current section | Navigation config, route middleware expectations, or known-route data drifted after a move | Update navigation and redirects, refresh known-route data when needed, then run the full site check. |
| Review keeps flagging voice or terminology | The page mixed content types, led with API capability instead of reader goals, or used non-canonical terms | Re-outline mixed sections, use canonical terminology, then rerun the docs-reviewer flow. |
| Code looks plausible but audit fails | Imports, parameter names, or method names were inferred instead of verified | Verify against SDK source for each language. If evidence is unavailable, remove the example or surface the gap. |

If a problem crosses domains, fix the routing first. SDK behavior issues belong
to the relevant SDK skill; docs-search MCP runtime belongs to mcp-server. Return
to docs-site only for the page, metadata, navigation, generated-doc, or review
work.
