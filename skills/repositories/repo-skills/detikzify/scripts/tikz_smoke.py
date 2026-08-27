#!/usr/bin/env python3
"""Compile and rasterize a tiny TikZ document through DeTikZify's helper."""

from textwrap import dedent

from detikzify.infer import TikzDocument


TIKZ_SNIPPET = dedent(
    r"""
    \documentclass{article}
    \usepackage{tikz}
    \begin{document}
    \begin{tikzpicture}
      \draw (0,0) -- (1,1);
    \end{tikzpicture}
    \end{document}
    """
).strip()


def main() -> None:
    doc = TikzDocument(TIKZ_SNIPPET, timeout=60)
    compiled = doc.compile()
    image = doc.rasterize()
    print(f"status={compiled.status}")
    print(f"has_pdf={compiled.pdf is not None}")
    print(f"rasterizable={doc.is_rasterizable}")
    print(f"has_content={doc.has_content}")
    print(f"image_size={getattr(image, 'size', None)}")
    if compiled.status != 0 or compiled.pdf is None or image is None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
