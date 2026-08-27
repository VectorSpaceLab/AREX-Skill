# Data-preparation troubleshooting

- **Concept list is not a JSON list**: the manifest loader expects an array of concept objects.
- **Missing concept fields**: each concept needs `instance_prompt`, `class_prompt`, `instance_data_dir`, and `class_data_dir`.
- **Instance directory does not exist**: the training dataset walks `instance_data_dir` directly, so fix the path before training.
- **Image list and caption list disagree**: the real-prior layout must keep the same ordering and line count in `images.txt` and `caption.txt`.
- **Blank caption lines**: remove empty lines so the class-image count and caption count stay aligned.
- **Wrong directory-vs-file mode**: a generated-prior layout uses an image directory; a real-prior bundle uses list files. Do not mix the two.
- **Retrieval is blocked by network policy**: use a local bundle or wait until network access is allowed.
- **Training later complains about token counts**: that is a training-route issue; route to the training sub-skill after the layout is fixed.
