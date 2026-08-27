# Configuration and Data Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Config parser fails before Ludwig validation | Invalid YAML/JSON syntax | Reformat with explicit indentation and quote strings that contain `:` or special characters. |
| `input_features` or `output_features` missing | Config is incomplete | Add non-empty lists with `name` and `type` for each feature. |
| Dataset column not found | Feature `name`/`column` does not match file header | Inspect headers and either rename the data column or set `column`. |
| Generated config references wrong target | Natural-language prompt was ambiguous | Specify dataset columns, target name, prediction type, and any modality constraints. |
| `generate_config` cannot import provider SDK or authenticate | Missing provider package/API key | Install/configure the chosen provider or draft config manually; do not retry blindly. |
| Preprocess consumes too much memory | Large data or media decode | Use a tiny sample first, choose lazy/media options carefully, or move to a larger machine. |

Run the bundled validators first; they produce simpler messages than full training failures.
