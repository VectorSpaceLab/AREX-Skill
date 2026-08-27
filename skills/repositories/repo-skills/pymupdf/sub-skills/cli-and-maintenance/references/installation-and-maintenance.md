# Installation and Maintenance

Start with a wheel install. If no wheel is available, source build requires a C/C++ toolchain and builds MuPDF. Custom/system MuPDF builds are maintainer workflows because PyMuPDF and MuPDF versions/configs must match.

For focused maintainer checks, start with import, CLI help, open/save, text/table, pixmap/image, edit/redaction, and embedded-file cases before the full suite. The full suite can require pytest, fontTools, psutil, Pillow, `pymupdf-fonts`, and other tooling.

Do not run release, Docker/cibuildwheel, sudo/system-install, or broad environment-mutation workflows without explicit authorization.
