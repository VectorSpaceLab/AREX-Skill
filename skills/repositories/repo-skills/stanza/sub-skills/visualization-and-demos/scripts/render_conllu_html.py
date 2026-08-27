#!/usr/bin/env python3
"""Render CoNLL-U from stdin or a file into a self-contained HTML review page."""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path
from typing import Optional

from stanza.utils.conll import CoNLL

DEFAULT_TITLE = "Stanza CoNLL-U Review"


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="render_conllu_html.py",
        description=(
            "Read CoNLL-U from stdin or a file and render a simple self-contained HTML "
            "table for sentence, token, head, deprel, and NER review."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  render_conllu_html.py input.conllu -o review.html\n"
            "  cat input.conllu | render_conllu_html.py > review.html\n"
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Path to a CoNLL-U file, or - to read from stdin (default).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output HTML path, or - to write to stdout (default).",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help="Page title to place in the generated HTML.",
    )
    return parser.parse_args(argv)


def read_conllu_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()

    path = Path(source).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Input path is a directory: {path}")
    return path.read_text(encoding="utf-8")


def parse_misc_value(misc: Optional[str], key: str) -> Optional[str]:
    if not misc:
        return None
    prefix = f"{key}="
    for part in str(misc).split("|"):
        if part.startswith(prefix):
            value = part[len(prefix) :].strip()
            if not value or value == "_":
                return None
            return value
    return None


def extract_token_ner(token) -> str:
    for candidate in (
        getattr(token, "ner", None),
        getattr(token, "multi_ner", None),
        parse_misc_value(getattr(token, "misc", None), "NER"),
        parse_misc_value(getattr(token, "misc", None), "ner"),
    ):
        if candidate not in (None, "", "_"):
            return str(candidate)
    return "-"


def format_token_id(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, tuple):
        return "-".join(str(part) for part in value)
    return str(value)


def format_word_id(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, tuple):
        return ".".join(str(part) for part in value)
    return str(value)


def label_with_id(identifier: str, text: str) -> str:
    return f"{html.escape(identifier, quote=True)} — {html.escape(text, quote=True)}"


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def sentence_heading(sentence, index: int) -> str:
    heading = f"Sentence {index + 1}"
    extras = []
    sent_id = getattr(sentence, "sent_id", None)
    doc_id = getattr(sentence, "doc_id", None)
    if sent_id not in (None, ""):
        extras.append(f"sent_id={sent_id}")
    if doc_id not in (None, ""):
        extras.append(f"doc_id={doc_id}")
    if extras:
        return f"{heading} ({', '.join(extras)})"
    return heading


def sentence_text(sentence) -> str:
    text = getattr(sentence, "text", None)
    if text:
        return str(text)
    words = getattr(sentence, "words", None) or []
    return " ".join(str(getattr(word, "text", "")) for word in words if getattr(word, "text", None))


def build_word_index(sentence) -> dict:
    index = {}
    for word in getattr(sentence, "words", []) or []:
        if isinstance(getattr(word, "id", None), int):
            index[word.id] = word
    return index


def format_head(word, word_index: dict) -> str:
    head = getattr(word, "head", None)
    if head is None:
        return "-"
    if head == 0:
        return "0 — ROOT"
    if isinstance(head, int):
        head_word = word_index.get(head)
        if head_word is not None:
            return label_with_id(str(head), str(getattr(head_word, "text", "")))
        return str(head)
    return str(head)


def render_sentence_rows(sentence) -> str:
    word_index = build_word_index(sentence)
    rows = []
    for word in getattr(sentence, "words", []) or []:
        token = getattr(word, "parent", None)
        token_id = format_token_id(getattr(token, "id", getattr(word, "id", None)))
        token_text = str(getattr(token, "text", getattr(word, "text", "")))
        word_id = format_word_id(getattr(word, "id", None))
        word_text = str(getattr(word, "text", ""))
        head = format_head(word, word_index)
        deprel = getattr(word, "deprel", None) or "-"
        ner = extract_token_ner(token) if token is not None else "-"
        row_class = "root" if getattr(word, "head", None) == 0 else ""
        rows.append(
            "<tr class=\"%s\">"
            "<td data-label=\"Token\">%s</td>"
            "<td data-label=\"Word\">%s</td>"
            "<td data-label=\"Head\">%s</td>"
            "<td data-label=\"Deprel\">%s</td>"
            "<td data-label=\"NER\">%s</td>"
            "</tr>"
            % (
                row_class,
                label_with_id(token_id, token_text),
                label_with_id(word_id, word_text),
                html.escape(head, quote=True),
                html.escape(str(deprel), quote=True),
                html.escape(str(ner), quote=True),
            )
        )
    return "\n".join(rows)


def render_html(doc, title: str) -> str:
    sentences = list(getattr(doc, "sentences", []) or [])
    total_tokens = sum(len(getattr(sentence, "tokens", []) or []) for sentence in sentences)
    total_words = sum(len(getattr(sentence, "words", []) or []) for sentence in sentences)

    cards = []
    for index, sentence in enumerate(sentences):
        text = html.escape(sentence_text(sentence), quote=True)
        heading = html.escape(sentence_heading(sentence, index), quote=True)
        counts = (
            f"{pluralize(len(getattr(sentence, 'tokens', []) or []), 'token')} · "
            f"{pluralize(len(getattr(sentence, 'words', []) or []), 'word')}"
        )
        rows = render_sentence_rows(sentence)
        if not rows:
            rows = (
                '<tr><td colspan="5" class="empty">No word rows available for this sentence.</td></tr>'
            )
        cards.append(
            f"""
            <section class="sentence-card">
              <h2>{heading}</h2>
              <p class="sentence-meta">{html.escape(counts, quote=True)}</p>
              <p class="sentence-text">{text}</p>
              <table>
                <thead>
                  <tr>
                    <th>Token</th>
                    <th>Word</th>
                    <th>Head</th>
                    <th>Deprel</th>
                    <th>NER</th>
                  </tr>
                </thead>
                <tbody>
                  {rows}
                </tbody>
              </table>
            </section>
            """.strip()
        )

    body = "\n".join(cards) if cards else '<p class="empty">No sentences found in the input.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title, quote=True)}</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --panel: #ffffff;
      --border: #d8e0ea;
      --text: #172033;
      --muted: #5f6b7a;
      --accent: #0f766e;
      --root: #7c2d12;
      --empty: #6b7280;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 2rem;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .page {{ max-width: 1200px; margin: 0 auto; }}
    header.summary {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1rem 1.25rem;
      margin-bottom: 1rem;
    }}
    header.summary h1 {{ margin: 0 0 .25rem; font-size: 1.35rem; }}
    header.summary p {{ margin: 0; color: var(--muted); }}
    .sentence-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1rem 1.25rem 1.25rem;
      margin: 1rem 0;
      box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
    }}
    .sentence-card h2 {{ margin: 0 0 .25rem; font-size: 1.05rem; }}
    .sentence-meta {{ margin: 0 0 .5rem; color: var(--muted); font-size: .95rem; }}
    .sentence-text {{ margin: 0 0 .85rem; font-size: .98rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      border-top: 1px solid var(--border);
      padding: .55rem .65rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      font-size: .82rem;
      text-transform: uppercase;
      letter-spacing: .04em;
      color: var(--muted);
      border-top: 0;
    }}
    tbody tr.root td {{ background: rgba(15, 118, 110, .04); }}
    tbody tr.root td:nth-child(3) {{ color: var(--root); font-weight: 700; }}
    td:nth-child(4) {{ color: var(--accent); }}
    td:nth-child(5) {{ font-family: ui-monospace, SFMono-Regular, SFMono-Regular, Menlo, Consolas, monospace; }}
    .empty {{ color: var(--empty); font-style: italic; }}
    @media (max-width: 800px) {{
      body {{ padding: 1rem; }}
      table, thead, tbody, th, td, tr {{ display: block; }}
      thead {{ display: none; }}
      tr {{ border-top: 1px solid var(--border); padding-top: .25rem; }}
      td {{ border: 0; padding: .25rem 0; }}
      td::before {{
        content: attr(data-label);
        display: block;
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .04em;
        color: var(--muted);
        margin-bottom: .1rem;
      }}
      td:nth-child(5) {{ font-family: inherit; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="summary">
      <h1>{html.escape(title, quote=True)}</h1>
      <p>{pluralize(len(sentences), 'sentence')} · {pluralize(total_tokens, 'token')} · {pluralize(total_words, 'word')}</p>
    </header>
    {body}
  </div>
</body>
</html>
"""


def write_output(html_text: str, output: str) -> None:
    if output == "-":
        sys.stdout.write(html_text)
        return

    path = Path(output).expanduser()
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"Output path is a directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        conllu_text = read_conllu_text(args.input)
    except (FileNotFoundError, IsADirectoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not conllu_text.strip():
        html_text = render_html(type("EmptyDoc", (), {"sentences": []})(), args.title)
        try:
            write_output(html_text, args.output)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    try:
        doc = CoNLL.conll2doc(input_str=conllu_text)
    except Exception as exc:  # keep the helper user-friendly rather than a traceback
        print(
            "error: could not parse CoNLL-U input. "
            "Use documents-and-conllu to diagnose malformed rows.\n"
            f"detail: {exc}",
            file=sys.stderr,
        )
        return 2

    html_text = render_html(doc, args.title)
    try:
        write_output(html_text, args.output)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
