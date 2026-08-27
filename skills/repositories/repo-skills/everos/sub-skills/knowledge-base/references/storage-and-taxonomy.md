# Knowledge Storage and Taxonomy

## Hierarchy

EverOS knowledge uses three levels:

```text
L0 Category -> L1 Document -> L2 Topic
```

Every uploaded document becomes a self-contained Markdown directory under the scoped knowledge root:

```text
<memory-root>/<app>/<project>/knowledge/
  .taxonomy.md
  Technology/
    Q1_Report_d_a1b2c3d4e5f6/
      index.md
      1_Performance_Analysis.md
      _original/
        q1-report.pdf
```

`index.md` contains document metadata and summary. Topic Markdown files contain topic frontmatter and full extracted content. `_original/` preserves uploaded bytes when a file was supplied.

## Taxonomy

`.taxonomy.md` stores categories. EverOS ships default categories such as Technology, Science, Medical, Finance, Legal, Education, Business, Engineering, Arts, Sports, Travel, Food, Environment, Politics, History, Psychology, Agriculture, RealEstate, Media, and Others.

Operators may edit `.taxonomy.md` directly. Taxonomy reads happen at upload/category-list time, so category changes do not require a server restart. If no category matches, extraction falls back to `Others`.

## Source-of-truth behavior

Markdown is the authoritative document/topic store. SQLite rows and LanceDB indexes are derived by cascade. If derived indexes drift, use cascade operations from the cascade sub-skill rather than manually editing SQLite/LanceDB.

## Original files

The `_original/` directory stores the uploaded binary unchanged. Filenames are sanitized to one safe path component; traversal, NUL bytes, and overly long names are rejected before writing.

Lifecycle:
- Create stores `_original/<filename>` when file bytes exist.
- Replace clears/replaces the document directory after backup.
- Delete removes the whole document directory.
- Patch category moves the entire directory so `_original/` follows.
