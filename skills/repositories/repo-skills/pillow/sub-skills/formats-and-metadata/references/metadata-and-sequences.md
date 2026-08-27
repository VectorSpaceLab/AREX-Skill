# Metadata and Sequences

Pillow metadata is intentionally format-specific. `Image.info` is a dictionary of fields read by the plugin, but many operations create a new `Image` without preserving the original file handle, `format`, or plugin-specific attributes. Treat metadata preservation as an explicit part of every save pipeline.

## `Image.info` and Format State

- `Image.open()` reads enough bytes to identify the file and populate basic metadata; pixel data remains lazy until `load()` or another operation requires it.
- Single-frame images opened from a path may close their file after `load()`. Multi-frame images keep the file open so `seek()` can read later frames.
- `copy()`, `convert()`, transforms, and many image operations can remove `format`, `fp`, plugin-specific methods, and some metadata context.
- Save parameters are not inferred uniformly from `info`; pass values explicitly when they matter.
- For file-like output, pass `format=` because Pillow cannot infer a save format from an extension.

A robust pattern is to collect metadata before transforms:

```python
from PIL import Image

with Image.open("source.jpg") as im:
    im.load()
    metadata = {
        "icc_profile": im.info.get("icc_profile"),
        "exif": im.getexif(),
        "xmp": im.info.get("xmp"),
        "dpi": im.info.get("dpi"),
    }
    out = im.convert("RGB")

save_kwargs = {key: value for key, value in metadata.items() if value}
out.save("target.jpg", format="JPEG", quality=90, **save_kwargs)
```

## EXIF

Use `im.getexif()` for EXIF read/write workflows. It returns an `Image.Exif` mapping that can be inspected, edited, deleted from, and serialized with `tobytes()` when a plugin expects raw EXIF bytes.

- Use `PIL.ExifTags.Base`, `GPS`, `Interop`, `IFD`, and related enums for readable tag names.
- `ExifTags.TAGS` and `ExifTags.GPSTAGS` map numeric tag IDs to names for legacy code.
- Access nested IFDs with `exif.get_ifd(ExifTags.IFD.GPSInfo)`, `ExifTags.IFD.Exif`, `ExifTags.IFD.MakerNote`, `ExifTags.IFD.Interop`, or `ExifTags.IFD.IFD1`.
- Orientation is `ExifTags.Base.Orientation`. If EXIF orientation is absent, Pillow may infer it from XMP orientation in `getexif()`.
- `ImageOps.exif_transpose()` belongs to the core transform flow, but format agents should remember that applying orientation changes pixels and should usually remove or update the orientation tag before saving.
- JPEG, PNG, WebP, AVIF, and TIFF can carry EXIF, but support and exact storage differ by format.

Preserve EXIF without accidentally dropping it:

```python
from PIL import Image, ExifTags

with Image.open("photo.jpg") as im:
    exif = im.getexif()
    exif[ExifTags.Base.Software] = "Pillow"
    rgb = im.convert("RGB")
    rgb.save("photo-out.jpg", format="JPEG", exif=exif, icc_profile=im.info.get("icc_profile"))
```

## ICC Profiles and Color Management

ICC bytes are usually stored as `im.info["icc_profile"]`. Saving a converted/copy image will not automatically attach the profile unless the target plugin does so for that option.

- Preserve embedded ICC with `icc_profile=im.info.get("icc_profile")` when the target format supports it.
- Use `features.check("littlecms2")` before relying on `PIL.ImageCms` transforms.
- `ImageCms.profileToProfile(im, inputProfile, outputProfile, renderingIntent=..., outputMode=..., inPlace=False, flags=...)` converts between profiles.
- `ImageCms.getOpenProfile()`, `createProfile()`, `buildTransform()`, and `applyTransform()` support more advanced workflows.
- `ImageCms.PyCMSError` usually indicates an invalid profile path/bytes, unsupported mode, or unavailable LittleCMS support.

ICC-capable save targets include JPEG, PNG, TIFF, WebP, and AVIF. PDF/EPS workflows may not preserve raster metadata semantics in the same way.

## XMP

XMP appears as bytes in `im.info["xmp"]` for formats that expose it. Some formats may use `"XML:com.adobe.xmp"` internally. `im.getxmp()` parses XMP into a dictionary when `defusedxml` is installed.

- `getxmp()` returns `{}` if no XMP is present.
- If `defusedxml` is unavailable, `getxmp()` warns and returns `{}`.
- Save XMP explicitly with `xmp=...` for formats such as WebP and AVIF that support it.
- XMP may contain orientation data; reconcile it with EXIF orientation to avoid double rotation or inconsistent viewers.

## PNG Text and Palettes

PNG text chunks are exposed through `Image.text`, while some decoded text may also appear in `info`. Use `PngImagePlugin.PngInfo` to write text chunks.

- `tEXt`, `zTXt`, and `iTXt` chunks can be read.
- Pillow limits decompressed PNG text chunk sizes for safety.
- `P` images may carry palette transparency as an index or a bytes table in `info["transparency"]`.
- `Image.apply_transparency()` can move `P`-mode transparency into the palette alpha data and remove the `transparency` key.

## TIFF Tags

TIFF exposes deeper metadata than most formats.

- Use `im.tag_v2` for current TIFF tag access; values are decoded using modern tag metadata.
- Use `PIL.TiffTags.lookup(tag)` or `TiffTags.TAGS_V2` to map IDs to names.
- Use `TiffImagePlugin.ImageFileDirectory_v2()` for deliberate `tiffinfo` writes, especially when tag types matter.
- Multiple values should be tuples, and rational values can use `TiffImagePlugin.IFDRational`.
- `tiffinfo` is the primary save option for TIFF tags; `exif=` is an alternate keyword for consistency with other formats.
- BigTIFF output requires `big_tiff=True`.

## Multi-Frame Images

Use `ImageSequence.Iterator(im)` for GIF, APNG, TIFF, WebP, AVIF, PDF inputs where applicable, and other registered sequence plugins. Use `ImageSequence.all_frames()` when you need independent copies of all frames, optionally transformed by a callback.

Important rules:

- `Iterator` yields the source image object after seeking; copy frames if you need to store them.
- `seek(frame)` raises `EOFError` beyond the last frame; `Iterator[index]` raises `IndexError` for invalid frames.
- `im.n_frames` and `im.is_animated` are available for many sequence formats, but always handle absent attributes for single-frame formats.
- Keep the original file open until all required frames are loaded or copied.
- For save, the base image is frame 0 and `append_images` starts at frame 1.

Frame collection pattern:

```python
from PIL import Image, ImageSequence

with Image.open("input.gif") as im:
    frames = [frame.copy() for frame in ImageSequence.Iterator(im)]
    durations = [frame.info.get("duration", im.info.get("duration", 0)) for frame in ImageSequence.Iterator(im)]
    loop = im.info.get("loop", 0)

frames[0].save("output.gif", save_all=True, append_images=frames[1:], duration=durations, loop=loop)
```

## Animation Metadata

- GIF: `duration`, `loop`, `background`, `transparency`, `disposal`, `comment`, and palette handling matter.
- APNG: `default_image`, `loop`, `duration`, `disposal`, and `blend` matter. If `default_image=True`, per-frame lists exclude the default image.
- WebP: `duration`, `loop`, `background`, `timestamp`, key-frame options, and mixed/lossless settings matter.
- AVIF: `duration` and sequence frame handling matter; codec availability can vary.
- TIFF/PDF: `save_all=True` and `append_images` create multi-page documents, not web-style animations.

When converting animations between formats, normalize frame sizes, modes, alpha handling, duration list length, and loop semantics before saving.
