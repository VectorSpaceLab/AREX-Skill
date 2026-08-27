# Dataset Labeling Troubleshooting

Use this when `base_model.label(...)` creates no files, writes an unexpected dataset, fails mid-run, or needs optional plugin/backend/credential decisions.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Output folder is empty or has no labels | Input files do not match `extension`; default is `.jpg` only | Pass `extension=".png"` or convert inputs. Check with a small folder before a full run. |
| `ValueError: Ontology is empty` | `CaptionOntology({})` or parsed CLI ontology was empty | Provide at least one prompt-to-class mapping such as `{"milk bottle": "bottle"}`. |
| `Class not found in ontology` or `Prompt not found in ontology` | Code asks for a prompt/class absent from the ontology | Print `ontology.prompts()` and `ontology.classes()`; update mappings or downstream class names. |
| `Expected detections to have confidence values.` | `record_confidence=True` but the model returned `Detections` without `confidence` | Add confidence scores in the model/plugin or disable `record_confidence`. |
| Very high memory use or process killed | Labeling stores detections for all images before export; docs warn large datasets are not optimized | Label a few hundred images at a time, write distinct output folders, then combine after validation. |
| Train or valid split is empty | Too few images for the 80/20 split | Use at least two images for smoke tests and enough images for real training. |
| SAHI is slow or produces duplicate boxes | Slicing runs more predictions and may need NMS tuning | Use `sahi=True` only for small-object cases; try `NmsSetting.CLASS_AGNOSTIC` or plugin-level thresholds. |
| ImportError for a base/target model | Core `autodistill` does not include plugin implementations | Install the specific plugin package and verify it independently; do not install every plugin by default. |
| CUDA/VRAM/model download failure | Concrete plugin requires hardware, weights, or compatible framework wheels | Narrow to a CPU-capable plugin, move to compatible hardware, or explicitly prepare the plugin backend. |
| Roboflow login/upload prompt or failure | `human_in_the_loop=True` needs network and credentials | Obtain explicit approval and credentials, or run labeling locally with `human_in_the_loop=False`. |
| Docs mention `label_folder` or `predict_sahi` | Public docs are stale relative to this source snapshot | Use source-verified `label()` and `sahi_predict()` unless a concrete plugin documents an alias. |

## Debug Order

1. Run the root install smoke script.
2. Run `scripts/create_tiny_detection_dataset.py --keep` from this sub-skill.
3. Validate input extension and ontology mapping.
4. Run one real prediction with the chosen plugin before labeling a folder.
5. Label a tiny input folder before a large batch.
6. Only then add target-model training or Roboflow upload.
