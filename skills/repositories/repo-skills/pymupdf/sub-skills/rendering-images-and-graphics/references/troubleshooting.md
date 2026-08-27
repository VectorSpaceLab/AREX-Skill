# Rendering/Image Troubleshooting

- Wrong resolution: use `dpi=` for direct target resolution; `matrix` scales by factors.
- Wrong clip: clip is in page coordinates; intersect with `page.rect`.
- Transparent background: keep `alpha=False` unless alpha is required.
- Annotations appear in thumbnails: set `annots=False`.
- Extracted images are duplicates: deduplicate by xref or digest.
- Soft-mask transparency lost: inspect `smask` and combine mask/pixmap.
- `pil_*` errors: install Pillow or use direct Pixmap output.
