# PyMuPDF CLI Reference

Use `python -m pymupdf` or `pymupdf`.

Subcommands: `show`, `clean`, `join`, `extract`, `embed-info`, `embed-add`, `embed-del`, `embed-upd`, `embed-extract`, `embed-copy`, `gettext`, and `internal`.

Examples:

```bash
python -m pymupdf --help
python -m pymupdf show -metadata input.pdf
python -m pymupdf gettext -mode layout -pages 1-2 -output text.txt input.pdf
python -m pymupdf clean -garbage 3 -compress input.pdf output.pdf
python -m pymupdf join -output joined.pdf a.pdf b.pdf
```

Use explicit output paths. For `join`, each input can be `filename[,password[,pages]]`. Embedded-file extraction should use explicit `-output` unless stored filenames are trusted.
