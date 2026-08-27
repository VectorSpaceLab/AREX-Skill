---
name: extensions
description: "Build and customize Kotaemon/ktem components, indexes, pages,
  settings, plugins, and project templates for developers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kotaemon Extensions

Use this sub-skill when the task is to add or review developer-facing Kotaemon extensions: custom `BaseComponent` pipelines, file indexing/retrieval classes, `flowsettings.py` registrations, ktem app pages, settings surfaces, pluggy extensions, or project/component templates.

## Use This For

- Creating or reviewing `BaseComponent` classes with typed params/nodes and a `run(...)` method.
- Registering custom reasoning/indexing/retrieval pipelines through `flowsettings.py` dotted paths.
- Extending file indexes with custom indexing pipelines, retriever pipelines, selector/index pages, or new `BaseIndex` types.
- Adding developer settings exposed in the Settings page through `get_user_settings`, `get_admin_settings`, `get_info`, and `get_pipeline` contracts.
- Packaging ktem pluggy extensions with `ktem_declare_extensions` and project scaffolds based on Kotaemon templates.

## Route Elsewhere

- End-user app install, launch, `.env`, login, Docker, PDF.js, update, or data migration: use `../app-deployment/SKILL.md`.
- Provider credentials, endpoint shapes, local model servers, LLM/embedding/reranking manager setup, or GraphRAG provider config: use `../model-providers/SKILL.md`.
- File readers, OCR/table parser implementation details, splitters, and document metadata validation: use `../document-ingestion/SKILL.md`.
- Core retrieval, reranking, QA, citation, `Document`, `RetrievedDocument`, vectorstore/docstore internals, and RAG pipeline composition: use `../rag-core/SKILL.md`.

## Fast Workflow

1. Identify the extension surface: component, reasoning pipeline, file-index pipeline, retriever, index type, page/UI, pluggy package, or scaffold template.
2. Use `references/component-development.md` for the `BaseComponent` contract, typed params/nodes, prompt UI settings, and contribution clues.
3. Use `references/index-extension.md` for `BaseIndex`, `BaseFileIndexIndexing`, `BaseFileIndexRetriever`, `KH_INDEX_TYPES`, `KH_INDICES`, and `FILE_INDEX_*` overrides.
4. Use `references/plugin-ui-extension.md` for ktem pages/settings integration, pluggy declarations, and template packaging.
5. Run the bundled static checker before reviewing or registering a new component/template:

```bash
python skills/kotaemon/sub-skills/extensions/scripts/scaffold_component_check.py --path <component-file-or-template-dir>
```

## Review Checklist

- Component classes subclass `kotaemon.base.BaseComponent` or a ktem index base and implement the required `run`/factory signatures.
- Public settings dictionaries use supported Gradio component ids: `text`, `number`, `checkbox`, `dropdown`, `radio`, or `checkboxgroup`.
- Every dotted path in `flowsettings.py` is importable from the app working directory and points to a class, not a module.
- Custom file-index pipelines surface user settings with stable keys and read index/admin settings through `get_pipeline(...)` rather than global state.
- Pluggy declarations use ids without `.` or `/`, match the `ktem` hook namespace, and expose callbacks/settings in the expected dictionary shape.
- Templates include packaging files and a discoverable Python package so generated projects can be installed before `flowsettings.py` references them.

## Bundled References

- `references/component-development.md` - `BaseComponent` contract, params/nodes, prompt UI, project template, and contribution workflow.
- `references/index-extension.md` - custom index, file-index pipeline, retrieval, UI class, and `flowsettings.py` registration points.
- `references/plugin-ui-extension.md` - app/page lifecycle, Settings tab rendering, pluggy protocol, and template packaging.
- `references/troubleshooting.md` - static diagnosis for missing subclasses, signatures, settings, dotted paths, hooks, and templates.

## Bundled Script

- `scripts/scaffold_component_check.py` - offline static checker for a component file or template directory; it parses Python with `ast`, scans text files, executes no project code, and exits nonzero for hard compatibility failures.
