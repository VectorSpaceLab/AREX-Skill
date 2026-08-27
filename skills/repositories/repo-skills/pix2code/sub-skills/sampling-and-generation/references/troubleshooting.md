# Sampling and Generation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `pix2code.json`, `pix2code.h5`, `meta_dataset.npy`, or `words.vocab` | The trained model directory is incomplete. | Run the bundled artifact checker and recover the missing file before sampling. |
| `ValueError` or shape mismatch while loading metadata | `meta_dataset.npy` does not match the model architecture or vocabulary. | Recreate the artifact directory from the same training run or inspect the metadata before loading. |
| OpenCV cannot read the screenshot | The input image path is wrong or the file is not a readable PNG. | Fix the path or convert the image to PNG first. |
| `model.load_weights` fails | The HDF5 weights do not match the JSON architecture or the files were mixed from different runs. | Keep the architecture, weights, metadata, and vocabulary from the same training output directory. |
| Historical all-in-one shell wrapper fails | The wrapper expects pretrained-result folders that are not part of a normal checkout and is tied to a source-tree layout. | Use the bundled checker and the inference workflow notes to validate artifacts before adapting any checkout-specific command. |
| Generated DSL looks random or incomplete | pix2code is a research prototype; its predictions depend heavily on the trained weights and search strategy. | Try the correct artifact directory, use beam search, or treat the output as an educational scaffold rather than a final UI. |
