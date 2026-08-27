# Format Reference

Pillow identifies input images from file contents. It chooses an output encoder from the destination extension unless `format=` is supplied. For `BytesIO`, sockets, temporary files without a recognized suffix, or intentionally mismatched extensions, always pass `format="..."`.

## Capability Names

Use `PIL.features` before choosing optional formats:

| Capability | Check | Used for |
| --- | --- | --- |
| JPEG | `features.check("jpg")` | JPEG/JFIF/Adobe JPEG encode/decode |
| JPEG 2000 | `features.check("jpg_2000")` | `.jp2`, `.j2k`, `.jpx` via OpenJPEG |
| zlib | `features.check("zlib")` | PNG and zlib-compressed data |
| libtiff | `features.check("libtiff")` | compressed TIFF read/write |
| WebP | `features.check("webp")` | WebP stills and animations |
| AVIF | `features.check("avif")` | AVIF stills and sequences |
| LittleCMS | `features.check("littlecms2")` | ICC color management via `ImageCms` |

`features.version(name)` returns a version string or `None` when unavailable. Some values are compile-time facts, so a format may fail at import or encode time if system libraries are inconsistent.

## PNG

Best for lossless images, alpha, palettes, text chunks, ICC profiles, and broad web compatibility.

- Reads/writes `1`, `L`, `LA`, `I`, `P`, `RGB`, and `RGBA`.
- Requires zlib for normal support.
- Reads EXIF, but PNG EXIF may not appear in `im.info` until `im.load()` has run.
- `im.info` may include `chromaticity`, `gamma`, `srgb`, and `transparency`.
- Text chunks are exposed through `Image.text`; Pillow limits individual and total decompressed text chunk sizes to reduce decompression-bomb risk.
- Save options: `optimize`, `transparency`, `dpi`, `pnginfo`, `compress_level`, `icc_profile`, `exif`, experimental `bits`, and experimental `dictionary`.
- `optimize=True` forces maximum compression behavior, so `compress_level` no longer controls speed/size in the usual way.

For APNG, use `save_all=True` or non-empty `append_images`. Options include `default_image`, `append_images`, `loop`, `duration`, `disposal`, and `blend`; list-valued frame options must match the number of animation frames.

## JPEG

Best for lossy photographic output without alpha.

- Reads JPEG, JFIF, and Adobe JPEG containing `L`, `RGB`, or `CMYK` data.
- Save to JPEG only after resolving alpha. For transparent input, composite over a background or explicitly drop alpha with `convert("RGB")`.
- `im.info` may include `jfif`, `jfif_version`, `jfif_density`, `jfif_unit`, `dpi`, `adobe`, `adobe_transform`, `progression`, `icc_profile`, `exif`, and `comment`.
- Save options: `quality`, `optimize`, `progressive`, `dpi`, `icc_profile`, `exif`, `keep_rgb`, `subsampling`, restart markers, `qtables`, `streamtype`, and `comment`.
- Avoid `quality=100` unless required; values above 95 create large files with little visual benefit.
- `quality="keep"` and `subsampling="keep"` are only valid when saving an existing JPEG-like source.
- `keep_rgb=True` stores RGB rather than converting to YCbCr; combining it with chroma subsampling raises an `OSError`.

## GIF

Best for simple palette animations and compatibility.

- Reads GIF87a/GIF89a and writes LZW-encoded GIF.
- GIF starts in `L` or `P`; later frames may become `RGB` or `RGBA` because frames can have different palettes.
- `GifImagePlugin.LOADING_STRATEGY` can force RGB from the first frame or keep `P` where possible.
- `im.info` may include `background`, `transparency`, `version`, `duration`, `loop`, `comment`, and `extension`.
- Save animation with `save_all=True`, `append_images`, `duration`, and `loop`.
- Save options include `include_color_table`, `interlace`, `disposal`, `palette`, `optimize`, `transparency`, `duration`, `loop`, and `comment`.
- `optimize` can compress palettes and mark unchanged pixels transparent; disable or control palette data when exact palette behavior matters.

## TIFF

Best for multi-page documents, scientific/archival images, high-bit-depth data, and explicit tags.

- Reads/writes TIFF; compressed TIFF requires libtiff for reliable modern behavior.
- Reads striped/tiled images, pixel/plane interleaving, and multi-band data.
- `im.info` may include `compression`, `dpi`, and `resolution`.
- Use `im.tag_v2` for TIFF metadata; keys are numeric TIFF tag IDs and values may be strings, numbers, tuples, or `IFDRational`.
- Use `TiffTags.lookup(tag)` or `TiffTags.TAGS_V2` to name tags.
- Save options: `save_all`, `append_images`, `tiffinfo`, `exif`, `big_tiff`, `compression`, `quality`, `description`, `software`, `date_time`, `artist`, `copyright`, `icc_profile`, `resolution_unit`, `resolution`, `x_resolution`, `y_resolution`, and `dpi`.
- Compressions such as `jpeg`, `tiff_lzw`, `packbits`, `webp`, and `zstd` require matching libtiff capabilities.

## WebP

Best for modern lossy/lossless stills and animations with optional metadata.

- Requires libwebp.
- Supports still images and animations through the WebP animation decoder/encoder.
- `im.info` may include `loop`, `background`, `icc_profile`, `exif`, `xmp`, per-frame `timestamp`, and per-frame `duration` after loading/seeking frames.
- Still save options: `lossless`, `quality`, `alpha_quality`, `method`, `exact`, `icc_profile`, `exif`, and `xmp`.
- Sequence save options: `save_all`, `append_images`, `duration`, `loop`, `background`, `minimize_size`, `kmin`, `kmax`, and `allow_mixed`.
- WebP maximum dimensions and encoder errors are library-dependent; diagnose with feature/version checks and small reproduction saves.

## AVIF

Best for compact modern still images and AVIF sequences, when deployment supports it.

- Requires AVIF support in Pillow and available libavif codecs.
- Reads/writes AVIF and AVIF sequence images.
- Saves only 8-bit AVIF; decoded AVIF images are 8-bit RGB/RGBA.
- `im.info` may include `icc_profile`, `exif`, `xmp`, per-frame `timestamp`, and per-frame `duration`.
- Save options: `quality`, `subsampling`, `speed`, `max_threads`, `range`, `codec`, `tile_rows`, `tile_cols`, `autotiling`, `alpha_premultiplied`, `advanced`, `icc_profile`, `exif`, and `xmp`.
- Sequence save requires `save_all=True` or `append_images`; `duration` may be a scalar or per-frame list.
- `codec="auto"` selects an available encoder; explicit codecs such as `aom`, `rav1e`, or `svt` can fail if not available.

## JPEG 2000

Best for JP2/J2K workflows that need wavelet compression, quality layers, or domain-specific compatibility.

- Requires OpenJPEG support (`jpg_2000`).
- Reads/writes `L`, `LA`, `RGB`, `RGBA`, and `YCbCr`; CMYK support depends on OpenJPEG version.
- Supports raw codestreams (`.j2k`) and boxed files (`.jp2`, `.jpx`).
- Load-time controls include setting output `mode`, `reduce`, and `layers` before `load()`.
- Save options: `offset`, `tile_offset`, `tile_size`, `quality_mode`, `quality_layers`, `num_resolutions`, `codeblock_size`, `precinct_size`, `irreversible`, `mct`, `progression`, `signed`, `cinema_mode`, `no_jp2`, `comment`, and `plt`.
- Advanced options have strict numeric and structural requirements; validate with a round-trip read after saving.

## PDF and EPS

Use these for document-oriented output, not as general metadata-preserving raster containers.

- PDF saving supports single and multi-page output through `save_all=True` and `append_images`; image modes are encoded into PDF-friendly streams.
- PDF options include `append`, `save_all`, `append_images`, `resolution`/`dpi`, and document info fields such as title/author-like metadata depending on the writer options used.
- EPS can read embedded raster images directly. For other EPS files, Pillow needs Ghostscript available as `gs` or platform-specific equivalents.
- EPS `load(scale=...)` changes rasterization size; `load(transparency=True)` can request transparent rendering where supported.
- EPS writing supports `L`, `RGB`, and `CMYK`; Ghostscript may convert color spaces while rasterizing input EPS.

## Format Identifier Reminders

Common `format=` strings are uppercase: `"PNG"`, `"JPEG"`, `"GIF"`, `"TIFF"`, `"WEBP"`, `"AVIF"`, `"JPEG2000"`, `"PDF"`, and `"EPS"`. Registered extension maps can be inspected with `Image.registered_extensions()` after `Image.init()`.
