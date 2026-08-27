# Multimodal RAG

Multimodal paths are optional and heavy. This reference describes their
contracts for planning and review; it does not authorize package installation,
model download, PDF conversion, GPU/MPS use, or execution. Confirm a populated
model cache, dependency environment, compute budget, and writable output paths
before any later run.

## Choose the representation

| Need | Representation | Retrieval unit | Recompute |
|---|---|---|---|
| Find ordinary images with text queries | One normalized CLIP vector per image | Image | Disabled; vectors are precomputed |
| Retrieve visually rich PDF pages | ColQwen2 or ColPali multi-vector page embedding | PDF page | Specialized multi-vector path |
| Explain where a query matches a page | Token/patch similarity map | Retrieved page region | Optional post-retrieval analysis |
| Generate an answer from retrieved pages | Separate vision-language generator | Retrieved images/pages | Optional and provider-owned |

Use text extraction document RAG for born-digital PDFs when layout, figures,
math, or scanned content are not needed. Do not pay the visual-PDF cost by
default.

## CLIP image retrieval

### Inputs and prerequisites

- A bounded image directory and explicit extension allowlist. The app-derived
  defaults are `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, and `.webp`, matched
  recursively and case-insensitively.
- Pillow, NumPy, and a Sentence Transformers installation capable of loading a
  CLIP model. The app-derived model identifier is `clip-ViT-L-14`.
- The model must already be approved and cached, or the user must separately
  authorize a download. This skill does not initiate one.
- Batch size and device memory budget. The app-derived batch default is 32.

### Passage and vector contract

For every successfully decoded image:

```text
text:     "Image: <name>\nPath: <path>"
metadata: image_path, image_name, image_dir
vector:   normalized float32 CLIP image embedding
id:       unique string aligned with vector order
```

The builder adds text and metadata, disables embedding recomputation, uses
cosine distance, and builds from precomputed vectors. Text queries must use the
matching CLIP text encoder and dimensionality. If custom code stages vectors in
a temporary file, remove that file in a `finally` block.

### Validation

1. Validate the directory and extension allowlist without opening images during
   planning.
2. During an authorized bounded run, decode each image to RGB and count failures.
3. Require at least one image after decoding. Verify unique IDs, metadata/vector
   order alignment, one vector per passage, consistent dimensions, finite
   values, float32 storage, and near-unit norm.
4. Search for an obvious visual concept and verify that returned metadata points
   to a real member of the approved corpus.
5. Never assume a filename-only passage proves visual retrieval; verify the
   query was embedded with the CLIP text tower.

## ColQwen2/ColPali visual-PDF retrieval

### Inputs and prerequisites

- One or more approved local PDFs. Encrypted, corrupt, or zero-page documents
  must fail clearly.
- `pdf2image` plus the Poppler executables (`pdfinfo`/`pdftoppm`) available on
  `PATH`.
- PyTorch, Pillow, `colpali_engine`, and a compatible Transformers 4.x release.
  The app-derived guard rejects Transformers 5.x and cites
  `transformers>=4.46.1,<5` as the supported range.
- A pre-approved local cache for `vidore/colqwen2-v1.0` or
  `vidore/colpali-v1.2`, or separate download authorization.
- Sufficient memory and storage for rendered pages, page-level multi-vectors,
  and optional figures. Device preference is CUDA, then Apple Metal Performance
  Shaders (MPS), then CPU. The app-derived dtypes are CUDA float16, MPS float32,
  and CPU bfloat16, with a CPU float32 retry for memory/offload failures.

### Pipeline

1. Render each PDF page to an image. The app-derived path uses 150 dots per inch.
2. Record `pdf_path`, `pdf_name`, one-based `page_number`, and optional saved
   `image_path` before embedding.
3. Encode every page into a matrix of visual token vectors with the selected
   model. Encode text queries with the paired processor/model.
4. Create a multi-vector collection whose dimension equals the final embedding
   axis; insert one document ID and vector matrix per page; build the index.
5. Search using the query matrix and return scored document IDs. Join IDs back
   to the external page metadata map before presenting results.

The easy app-derived insertion path persists `doc_id`, optional page-image
`filepath`, and `colbert_vecs`; it does not itself demonstrate persistence of
all `pdf_name`/`page_number` metadata. Treat the external ID-to-page map as a
required artifact and validate it after reopen. Do not claim page citations if
that join cannot be recovered.

### Search, maps, and answers

- Use the same model family at build and search.
- Keep first-stage candidate count and final `top_k` bounded.
- Similarity maps are optional diagnostics, not answer evidence by themselves.
  Store each output with rank/query provenance and avoid overwriting ranks.
- The app-derived `ask` loop performs retrieval and explicitly leaves
  vision-language answer generation unimplemented. A Qwen-VL-style generator
  is a separate optional step; do not describe retrieval-only output as Q&A.

### Validation

- Every PDF produces at least one page and every page produces an embedding.
- Page IDs, embedding matrices, saved images, and metadata map have equal counts
  and deterministic order.
- Embedding dimensions and selected model type match after reopening the index.
- Retrieved IDs resolve to source PDF and one-based page number.
- A known page-level query returns the expected page in a tiny approved corpus.
- Similarity-map or answer-generation failures do not invalidate an otherwise
  successful retrieval test, but remain explicit optional gaps.

## Data layout

Use separate, non-overlapping locations:

```text
multimodal-run/
  inputs/             # approved immutable copies or mounts
  pages/              # optional rendered page cache
  indexes/            # LEANN or multi-vector index artifacts
  metadata/           # ID-to-image/page mapping and build manifest
  figures/            # optional retrieved-page and similarity-map outputs
```

The manifest should record model family/identifier, cache provenance, dtype,
device, rendering resolution, extension allowlist, input count, successful
item/page count, failures, vector dimension, and index base path. Do not record
credentials or private image content.

## Failure boundaries

- Missing Poppler, model packages, compatible Transformers, or an approved model
  cache is a blocked prerequisite—not a reason to install or download silently.
- Out-of-memory, MPS NaNs, or very slow CPU execution requires a smaller bounded
  corpus/batch or explicit device decision. Never keep retrying a heavy job.
- Corrupt images/PDFs are skipped only with counted diagnostics; zero successful
  items/pages is a hard failure.
- Metadata/vector count, ID order, model, or dimensional mismatch requires a
  clean staged rebuild. Do not patch around it by dropping citations.
