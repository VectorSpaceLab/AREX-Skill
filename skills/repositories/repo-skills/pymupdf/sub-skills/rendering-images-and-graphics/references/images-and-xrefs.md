# Images and Xrefs

Do not confuse page rendering with original embedded image extraction. For original PDF images, use `Page.get_images(full=True)`, deduplicate by xref, and call `Document.extract_image(xref)` or `Pixmap(doc, xref)`. `extract_image` preserves original bytes when possible and is often faster/smaller than rendering.

If an image has `smask`, reconstruct transparency with Pixmap mask logic. `Page.get_image_info(hashes=True, xrefs=True)` describes displayed images, and `Page.get_text("dict")` image blocks include displayed image bytes for all document types.
