# Editing API Reference

```python
Document.insert_pdf(docsrc, *, from_page=-1, to_page=-1, start_at=-1, rotate=-1, links=1, annots=1, widgets=1, join_duplicates=0, show_progress=0, final=1)
Document.insert_file(infile, from_page=-1, to_page=-1, start_at=-1, rotate=-1, links=True, annots=True, show_progress=0, final=1)
Page.search_for(text, quads=False)
Page.add_highlight_annot(quads=None, start=None, stop=None, clip=None)
Page.add_redact_annot(quad, text=None, fontname=None, fontsize=11, align=0, fill=None, text_color=None, cross_out=True)
Page.apply_redactions(images=2, graphics=1, text=0)
Page.add_widget(widget)
Document.embfile_add(name, buffer, filename=None, ufilename=None, desc=None)
Document.embfile_get(item)
```
