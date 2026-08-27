# Academic Document Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| PDF parser fails immediately | encrypted/corrupt/scanned PDF or missing parser dependency | open the PDF manually, convert scanned pages with OCR, try traditional parser or NOUGAT |
| formulas become garbled | traditional text extraction cannot preserve math | use Arxiv source if available, DOC2X, or NOUGAT for formula-heavy papers |
| DOC2X path fails | missing `DOC2X_API_KEY`, quota, network, or unsupported file | verify key presence, try GROBID/traditional fallback, keep intermediate output |
| GROBID is slow/unavailable | public GROBID service overloaded | configure a private GROBID service or switch parser |
| LaTeX compiled output missing | `pdflatex` or `latexdiff` unavailable or TeX project incomplete | run backend checks; install TeX Live/MiKTeX; compile original project first |
| LaTeX diff has bad highlights | project uses unusual macros or generated files | reduce scope to changed source files; inspect logs; provide text-only correction if compile is optional |
| Word file unreadable | legacy `.doc` or damaged document | convert to `.docx`; on non-Windows avoid pywin32-only paths |
| batch file query skips files | unsupported suffix, too large, or upload path expired | split files, convert formats, re-upload, and validate path with the bundled document input checker |
| Arxiv translation fails | ID typo, network/proxy, source unavailable, or LaTeX rebuild issue | verify ID/URL, enable proxy, fall back to PDF translation or summary |
| Google Scholar blocked | anti-scraping or page layout changed | ask for specific URLs/titles/Arxiv IDs or use a search backend through `conversation` |
