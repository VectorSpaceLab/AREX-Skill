# Troubleshooting Formats and Metadata

## Missing Codec or Feature

Symptoms include `UnidentifiedImageError`, `OSError` while opening/saving, warnings such as support not installed, or missing save handlers.

Checklist:

1. Check the exact capability name with `PIL.features.check(name)`.
2. Print versions with `PIL.features.version(name)`.
3. Inspect registered formats with the bundled `format_capability_report.py` or `python -m PIL`.
4. Confirm the plugin can save as well as open; read support is broader than write support.
5. Fall back to a more common format or ask the user to install/rebuild Pillow with the required system library.

Common capability mapping:

- PNG failures usually point to `zlib`.
- JPEG failures point to `jpg`.
- JPEG 2000 failures point to `jpg_2000` / OpenJPEG.
- Compressed TIFF failures point to `libtiff` and the specific compression codec.
- WebP failures point to `webp` / libwebp.
- AVIF failures point to `avif` and to available AV1 encoder/decoder codecs.
- ICC conversion failures point to `littlecms2` or invalid profile data.

## Unknown Extension or Wrong Save Format

`ValueError: unknown file extension` means Pillow could not infer the save format. This often happens with file-like objects, temporary files, uppercase/unusual suffixes, or extensionless paths.

Use:

```python
im.save(output_file_like, format="PNG")
im.save("asset.bin", format="WEBP")
```

Remember that opening identifies by content, but saving normally uses extension unless `format=` is explicit.

## Unsupported Save Parameter

Save parameters are plugin-specific. Passing a JPEG option to PNG or a WebP animation option to AVIF may be ignored or raise an exception depending on the plugin.

- Verify target format first: `format = (format or im.format or "").upper()`.
- Check the format reference for exact option names and accepted value types.
- For multi-frame output, ensure the format has a `SAVE_ALL` handler and pass `save_all=True` when needed.
- For strict encoders, catch `ValueError` and `OSError` and retry with simpler options.

Examples:

- `keep_rgb=True` and `subsampling` conflict for JPEG.
- AVIF `codec="aom"`, `"rav1e"`, or `"svt"` can fail if that encoder is unavailable.
- WebP `background` must be a valid RGBA tuple for animation saves.
- TIFF compression choices depend on libtiff and compiled codecs.
- APNG list-valued `duration`, `disposal`, and `blend` must match the number of actual animation frames.

## JPEG Transparency and Mode Mismatch

JPEG cannot store alpha channels or palette transparency. Saving `RGBA`, `LA`, or transparent `P` images directly as JPEG can fail or silently produce the wrong visual result if alpha is dropped incorrectly.

Use a deliberate background:

```python
from PIL import Image

rgba = im.convert("RGBA")
background = Image.new("RGBA", rgba.size, "white")
background.alpha_composite(rgba)
background.convert("RGB").save("out.jpg", format="JPEG", quality=90)
```

If preserving transparency matters, use PNG, WebP, AVIF, or TIFF instead.

## Metadata Lost After Copy, Convert, Resize, or Compose

Operations that create new images may not preserve `format`, `fp`, `info`, EXIF, ICC, XMP, palette, or plugin-specific state.

Fix:

1. Extract metadata before transforms.
2. Copy only metadata supported by the target format.
3. Pass metadata explicitly in `save()`.
4. Round-trip open the saved file and assert required metadata remains.

For EXIF orientation, decide whether to keep orientation metadata or apply it to pixels. Do not do both unless the target viewer expects it.

## EXIF Orientation Problems

Symptoms: output appears rotated twice, not rotated, or has inconsistent orientation between apps.

- Read orientation from `im.getexif().get(ExifTags.Base.Orientation)`.
- If applying orientation to pixels, use the core transform flow and remove or reset the orientation tag before saving.
- Check XMP orientation too; Pillow may infer EXIF orientation from XMP when EXIF lacks it.
- Save updated EXIF explicitly.

## Multi-Frame Save Only Wrote One Frame

Most formats save only the first frame unless told otherwise.

Fix:

```python
frames[0].save("out.webp", save_all=True, append_images=frames[1:], duration=durations, loop=0)
```

Also verify:

- `len(frames) > 1` and frames are independent copies if the source file is closed.
- Frame sizes are compatible with the target format.
- Modes are normalized (`RGB`/`RGBA` are common safe choices for WebP/AVIF; `P` can matter for GIF).
- Duration list length matches frame count.
- Loop semantics differ by format; `0` often means infinite for GIF/APNG/WebP.

## GIF Palette Surprises

GIF frames can have local palettes and may convert from `P` to `RGB`/`RGBA` while seeking. `optimize=True` can reduce palettes and mark unchanged pixels transparent.

- Choose `GifImagePlugin.LOADING_STRATEGY` when consistent frame modes matter.
- Copy converted frames before closing the source.
- Disable optimization or provide an explicit palette if palette indices matter.
- Preserve `duration`, `loop`, `disposal`, and `transparency` explicitly.

## PNG Text or EXIF Not Present

PNG EXIF may not be in `info` until after `load()`. PNG text chunks are in `Image.text`, not necessarily only in `info`.

- Call `im.load()` before reading PNG EXIF-sensitive metadata.
- Use `PngImagePlugin.PngInfo` to write PNG text chunks.
- Expect Pillow's decompressed text chunk limits to reject or truncate unsafe files.

## TIFF Tag or Compression Failures

- Use `im.tag_v2`, not the legacy `im.tag`, for new code.
- Use numeric tag IDs and `TiffTags.lookup()` for names.
- Use `ImageFileDirectory_v2` when field types are ambiguous.
- Use `IFDRational` for rational values.
- Check `features.check("libtiff")` before using compressed TIFF options.
- Round-trip read the output and inspect `tag_v2` and `info`.

## PDF and EPS External Dependencies

PDF writing is available through Pillow's PDF plugin, but PDF is not a full metadata-preserving image container. Multi-page PDF requires `save_all=True` and `append_images`.

EPS support has two modes:

- Embedded raster EPS can often be read directly.
- General EPS rasterization requires Ghostscript (`gs`, `gswin32c`, or `gswin64c`).

If EPS load fails or renders with unexpected colors/sizes, check Ghostscript availability, `EpsImagePlugin.gs_binary`, and `im.load(scale=...)`.

## AVIF, WebP, and JPEG 2000 Variance

Modern codecs vary by platform, library version, and compile options.

- AVIF may expose different encoders (`aom`, `rav1e`, `svt`) and decoders. Keep `codec="auto"` unless a specific codec is required.
- AVIF only saves 8-bit data and decodes as 8-bit RGB/RGBA.
- WebP dimensions, animation behavior, and exact/lossless handling depend on libwebp version.
- JPEG 2000 CMYK and PLT behavior depend on OpenJPEG version.

When a workflow must be portable, prefer PNG/JPEG/TIFF fallbacks or capability-gated branches.
