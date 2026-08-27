# Table Extraction

Use `tabs = page.find_tables(...)`; inspect `tabs.tables`, `tabs.cells`, and each `Table`. Durable outputs are `table.extract()` and `table.to_markdown()`. `table.to_pandas()` requires optional pandas, and DataFrame Markdown may need tabulate.

Start with `strategy="lines_strict"` or `"lines"` for ruled tables. For borderless tables, try text strategies. Use `add_lines`, `add_boxes`, and cached `paths` to help difficult pages. Copy table output before closing or mutating the page/document.
