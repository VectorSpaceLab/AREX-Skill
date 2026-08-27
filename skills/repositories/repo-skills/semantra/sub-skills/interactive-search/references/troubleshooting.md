# Interactive Search Troubleshooting

## Purpose

Use this reference when Semantra starts or indexes documents but the local web
UI, query behavior, result ranking, PDF navigation, or server routes are
confusing or failing.

## The search bar is yellow or results look stale

Likely cause: the query text or preference tags changed after the last search.

Recovery:

- Press Enter in the search bar or click the search icon.
- Remove stale positive/negative tags if they should no longer influence the
  query.
- Check filename filters and active-file filtering before blaming the model.

## Results are hidden or not sorted as expected

Likely causes:

- the filename filter is hiding files;
- the eye button restricts results to the active document;
- grouped-by-file view sorts files by average relevance, not individual windows;
- files are collapsed in the results pane.

Recovery:

- Clear the filter box.
- Toggle the eye button off.
- Switch between file view and individual-result view.
- Expand all files if grouped results appear empty.

## Scores seem low but results still appear

Semantra returns nearest windows for semantic queries; it does not filter to
zero results like a keyword engine. Scores around `0.50` can still be meaningful
for semantic similarity, depending on corpus and model.

Recovery:

- Try a more specific query.
- Use `+` and `-` query arithmetic.
- Positively tag one good result and negatively tag a misleading result, then
  rerun.
- If all results are poor, route to model/window selection rather than UI state.

## Exact words are not ranked first

Semantra ranks embedding similarity, not substring matches. Exact phrases can be
semantically weak in context, while paraphrases can score higher.

Recovery:

- Use concepts and paraphrases, not only exact words.
- Try smaller windows in the document-indexing sub-skill if passages are too
  broad.
- Switch models if the language/domain is mismatched.

## Port 8080 is busy

Symptom: startup fails and Semantra suggests specifying another port.

Recovery:

```sh
semantra --port 8081 <files>
```

If the user needs stable automation, choose an explicit port and pass it in all
local API calls.

## The user wants access from another machine

Default `127.0.0.1` listens only on the same machine. To listen on all
interfaces:

```sh
semantra --host 0.0.0.0 --port 8080 <files>
```

Warn first: Semantra can serve original file contents and extracted text to any
client that can reach the server. Use firewalling, trusted networks, or an SSH
tunnel instead of broad exposure when documents are sensitive.

## `/api/querysvm` or `--svm` fails

Likely causes:

- `scikit-learn` is missing;
- the selected model is asymmetric, such as `sgpt` or `sgpt-1.3B`;
- SVM is slower and heavier than default Annoy/exact kNN.

Recovery:

- Install `scikit-learn` only if SVM mode is required.
- Use a symmetric model such as `mpnet` or `minilm` for SVM.
- Prefer the default Annoy path for ordinary semantic search.

## PDF viewer does not navigate or highlight correctly

Likely causes:

- PDF text extraction differs from visual ordering;
- page-position JSON is missing or stale;
- `/api/pdfpositions`, `/api/pdfpage`, or `/api/pdfchars` fails;
- the browser cannot load rendered page images.

Recovery:

1. Confirm the file is detected as `filetype: "pdf"` by `/api/files`.
2. Confirm `/api/text` returns token chunks and `/api/pdfpositions` returns page
   positions.
3. Rebuild the PDF cache with `--force` if positions are missing or stale.
4. If text extraction itself is bad, preprocess with OCR outside Semantra.

## Static web app assets are missing

Symptoms: `/` returns 404/500, browser shows blank page, or JS/CSS files cannot
load.

Likely cause: Semantra's installed package cannot find bundled `client_public`
assets.

Recovery:

- Reinstall Semantra from a package that includes package data.
- If using a source checkout, build or restore the frontend assets before
  installing the package.
- Verify the package data path with the root installation inspection helper.

## `/api/explain` is slow or triggers model/API calls

The explain route embeds multiple modified versions of a selected result
window. With OpenAI mode, this can make external API calls; with local
transformer models, it can use noticeable CPU/GPU time.

Recovery:

- Reduce the number of results the UI needs to explain.
- Tune `--explain-split-count`, `--explain-split-divide`, or
  `--num-explain-highlights` only after the user understands the tradeoff.
- For OpenAI mode, consider cost implications before repeated explain calls.
