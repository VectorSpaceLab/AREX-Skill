# OCR and KIE troubleshooting

Use this guide for failures in `ocr_predictor` / `kie_predictor` inference. For file loading/export errors, CLI errors, custom model loading, or training issues, route to the sibling sub-skill named in `SKILL.md`.

## Fast triage

1. Can Python import `doctr`, `doctr.io.DocumentFile`, and the chosen predictor factory?
2. Are pages 3-D RGB `uint8` arrays shaped `(H, W, C)` or a `DocumentFile` list of such arrays?
3. Are weights expected to download? If not, set `pretrained=False` and `pretrained_backbone=False` for smoke checks, or prepare the cache before production.
4. Is the task OCR (`Document.pages[*].blocks`) or KIE (`KIEDocument.pages[*].predictions`)? Looking in the wrong field is common.
5. Did rotation/layout/table flags change the output schema or geometry shape?
6. Are detector/recognizer batch sizes too large for memory?

## Import or dependency errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` during `import doctr` | Core dependency missing from the active Python environment | Install/repair the package in the active environment; use the root environment-check script if available. |
| `ModuleNotFoundError` for visualization packages when calling `.show()` | Visualization extra is not installed | Do not use `.show()` in headless inference; install the visualization extra only when interactive display is required. |
| Error loading web pages through `DocumentFile.from_url` | HTML extra is missing | Route to document IO; install the HTML extra or use PDF/image inputs. |
| Torch CUDA/MPS error after `.to(device)` | Device is unavailable or incompatible | Probe `torch.cuda.is_available()` or `torch.backends.mps.is_available()` before moving the predictor; fall back to CPU for functional checks. |

## Weight download and offline behavior

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| First call hangs or fails on network access | `pretrained=True`, `pretrained_backbone=True`, layout/table flags, or orientation helpers require cached weights | Pre-cache weights, allow the download, or run a no-pretrained smoke check only. |
| `pretrained=False` still attempts a download | A pretrained backbone or orientation helper is still enabled | Use `pretrained_backbone=False`; keep `assume_straight_pages=True` for smoke tests or pass `disable_page_orientation=True` / `disable_crop_orientation=True` when using non-straight modes. |
| Output is empty or nonsensical in smoke mode | Randomly initialized models were used | This is expected with `pretrained=False`; validate only imports, factory construction, result type, and basic schema. |

## Input-shape failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: incorrect input shape: all pages are expected to be multi-channel 2D images.` | A page is grayscale, has an alpha-only shape, or a 4-D batch array was passed | Convert each page to RGB `(H, W, 3)` and pass a list of pages, not a pre-batched tensor. |
| Page count mismatch | The caller passed a single ndarray instead of a list/DocumentFile or filtered pages unexpectedly | Normalize to `pages = [page]` for a single image, then assert `len(result.pages) == len(pages)`. |
| Very slow inference on large PDFs/images | PDF pages were rasterized to large images or recognition generated many crops | Lower input resolution at IO time, lower `reco_bs`, use smaller architectures, or run fewer pages first. |

## Rotation and geometry surprises

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Downstream code expects two-point boxes but receives polygons | `assume_straight_pages=False` returns rotated boxes | Either handle four-point polygons or set `export_as_straight_boxes=True` when straight boxes are required. |
| Text quality is poor on rotated pages | Straight-page assumptions are wrong | Use `assume_straight_pages=False`, consider `straighten_pages=True`, and avoid disabling orientation helpers until quality is verified. |
| Boxes are in straightened-page coordinates instead of the original image | `straighten_pages=True` remapped page content unless original-coordinate preservation was enabled | Set `preserve_original_coords=True` when the output must align with the original page image. |
| Crop orientation metadata is always zero | Straight-page mode or disabled crop orientation was used | This is expected for straight mode; use non-straight mode only if rotated crops are part of the workload. |

## Layout and ignored-region issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `page.layout` is empty | `detect_layout` was not enabled, or the layout detector found no regions | Enable `detect_layout=True` and choose/verify a layout architecture; treat empty layout as possible, not exceptional. |
| `ignore_regions=[...]` appears to do nothing | No layout predictor was active or class names did not match detected layout labels | Pair it with `detect_layout=True` for OCR/KIE, or `detect_tables=True` for OCR, and inspect `region.type` values before choosing labels. |
| Useful text is missing after ignored regions | The ignored layout classes overlapped real text | Remove or narrow `ignore_regions`; inspect layout geometries and confidence. |
| Layout regions exist but exports/downstream code misses them | Consumer is reading only blocks/words | Read `page.layout` or `page.export()["layout"]`; route export details to document IO. |

## Table-aware OCR issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Table text vanished from normal blocks | With `detect_tables=True`, words assigned to table cells are removed from `page.blocks` | Read `page.tables`, `table.to_grid()`, or `page.export()["tables"]`. This is expected behavior. |
| `detect_tables=True` is slow | It enables layout detection and table-structure recognition in addition to OCR | Use it only for documents where structured tables are required; otherwise use `detect_layout=True` or plain OCR. |
| No tables are returned | The layout model did not label a `Table` region, or the table structure model found no cells | Verify `page.layout` contains table regions, test on a simpler page, and consider model/customization guidance. |
| KIE table extraction requested | `kie_predictor` has no `detect_tables` factory flag | Use OCR with `detect_tables=True` for tables, or use KIE only for class-grouped word predictions. |

## KIE-specific issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `result.pages[0].blocks` is missing or empty | KIE outputs predictions grouped by class, not OCR blocks | Use `result.pages[0].predictions[class_name]`. |
| Only one class appears in `predictions` | The detector is a standard text detector or custom multi-class weights were not loaded | Use a detector trained for the desired classes; route custom detector loading to models/customization. |
| Hook broke KIE output | Hook returned OCR-style lists instead of preserving KIE dictionaries | Hooks for KIE must preserve `{class_name: per-page_boxes}` structure and coordinate conventions. |
| Language metadata is empty or unreliable | Language detection depends on recognized text | Check recognition output quality first; do not use language metadata as a success criterion by itself. |

## Batch size and memory issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA out-of-memory during detection/layout | `det_bs` too high or pages too large | Lower `det_bs`, process fewer pages at a time, or reduce image resolution at input preparation. |
| CUDA out-of-memory during recognition | Dense pages generated many word crops and `reco_bs` is too high | Lower `reco_bs`; recognition memory scales with number and size of crops. |
| CPU inference is unexpectedly slow | Heavy architectures, layout/table flags, or large pages | Use smaller architectures, disable unneeded layout/table/orientation/language flags, and smoke-test with fewer pages. |
| Different throughput on GPU and CPU | Device movement or batch sizes differ | Log device choice, `det_bs`, `reco_bs`, and flags alongside results for reproducibility. |

## Output validation snippets

```python
from doctr.io.elements import Document, KIEDocument

if isinstance(result, Document):
    assert len(result.pages) == len(pages)
    for page in result.pages:
        exported = page.export()
        assert "blocks" in exported and "layout" in exported and "tables" in exported
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    assert isinstance(word.value, str)
                    assert 0.0 <= float(word.confidence) <= 1.0
elif isinstance(result, KIEDocument):
    assert len(result.pages) == len(pages)
    for page in result.pages:
        assert isinstance(page.predictions, dict)
        for class_name, predictions in page.predictions.items():
            assert isinstance(class_name, str)
            for pred in predictions:
                assert isinstance(pred.value, str)
                assert 0.0 <= float(pred.confidence) <= 1.0
else:
    raise TypeError(type(result))
```

For geometry validation, normalize both straight boxes and polygons to point arrays, then check finite values and expected relative coordinate ranges. Leave some tolerance for model or transform edge cases, but investigate values far outside `[0, 1]`.
