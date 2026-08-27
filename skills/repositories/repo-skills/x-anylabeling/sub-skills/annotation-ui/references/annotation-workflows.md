# Annotation UI Workflows

This reference distills the GUI and CLI behavior needed for manual annotation,
quality review, and task-specific UI modes. It is self-contained; do not rely on
external documentation during operation.

## 1. Launch and configuration

### Basic CLI commands

```bash
xanylabeling                 # launch the GUI
xanylabeling help            # print CLI help text
xanylabeling version         # print package version
xanylabeling checks          # print environment/system package facts
xanylabeling config          # print the active .xanylabelingrc path
```

The top-level `xanylabeling` command opens the GUI unless a utility subcommand
such as `help`, `version`, `checks`, `config`, or `convert` is supplied.
Conversion tasks are outside this sub-skill; route them to the conversion
sub-skill.

### GUI launch options

| Option | Operational use |
|---|---|
| positional `filename` | Image file, label JSON file, or image directory. A directory loads all supported images in that directory tree. |
| `--output`, `-O`, `-o` | If the value ends in `.json`, it is treated as a single output file; otherwise it is a label output directory. With autosave on, single-file output is ignored in favor of per-image labels, so prefer a directory. |
| `--config` | Either a path to a YAML config file or an inline YAML mapping string. If the value parses as a YAML object, it is treated as inline config; otherwise it is opened as a path. |
| `--work-dir` | Working directory for `.xanylabelingrc` and data subdirectories such as VQA/chatbot configs. Defaults to the user's home directory. Use a project work dir to keep GUI preferences isolated. |
| `--reset-config` | Clears Qt window/UI settings. Use for broken layouts or persisted GUI state. |
| `--logger-level` | One of `debug`, `info`, `warning`, `fatal`, `error`. Use `debug` only when diagnosing launch/config problems. |
| `--no-auto-update-check` | Disables startup update check. Useful in offline or restricted networks. |
| `--qt-platform` | Forces a Qt platform plugin such as `xcb` or `wayland`. Common WSL/Wayland fix: `--qt-platform xcb`. |
| `--qt-image-allocation-limit` | Overrides Qt's image allocation limit in MB. Qt's default is 256 MB; `0` disables the limit for very large images. |
| `--nodata` | Sets `store_data` false and prevents base64 image bytes from being embedded into label JSON. This is the recommended default for large datasets. |
| `--autosave` | Enables automatic save on edits. The default config already enables autosave. |
| `--nosortlabels` | Preserves label order instead of sorting label names. Useful when label order carries meaning. |
| `--flags` | Comma-separated image-level flag names or a path containing one flag per line. Stored under top-level `flags`. |
| `--labelflags` | YAML mapping string or file for label-specific shape flags. Stored in each shape's `flags` when selected. |
| `--labels` | Comma-separated labels or a path containing one label per line. Required when exact label validation is enabled. |
| `--validatelabel` | Only supported value is `exact`. Requires `--labels` or config `labels`; otherwise launch exits with an error. |
| `--keep-prev` | Reuses previous frame/image annotations while navigating. Disable before deleting labels/images. |

### Config behavior to remember

- The default config is saved as `.xanylabelingrc` in the selected work dir.
- CLI arguments override config values after the YAML config is loaded.
- Unknown config keys are skipped with warnings, not applied.
- Validated config values include:
  - `validate_label`: `null` or `exact` only.
  - `qt_image_allocation_limit`: `null` or a non-negative integer.
  - `shape_color`: `null`, `auto`, or `manual` only.
  - `labels`: duplicate labels are rejected.
- Inline YAML should be a mapping, for example:

  ```bash
  xanylabeling /data/images --config '{auto_save: true, store_data: false, validate_label: exact, labels: [cat, dog]}'
  ```

## 2. Importing and saving data

### Image directory import

- Shortcut: `Ctrl+U`.
- Directory import recursively scans supported Qt image formats plus HEIC/HEIF
  when available.
- The file list is naturally sorted when possible.
- If an output directory is configured, label existence/check status is read
  from that output directory using each image basename plus `.json`.
- Without an output directory, labels are loaded beside each image.

### Single image import

- Shortcut: `Ctrl+I`.
- Supported common formats include JPEG, PNG, BMP, WEBP, TIFF, plus formats
  reported by the local Qt image reader.
- A single image uses a sidecar label file with the same stem and `.json`
  extension unless `--output`/Change Output Directory is used.

### Single video import for frame annotation

- Shortcut: `Ctrl+O`.
- Common video formats include MP4, AVI, MOV, MKV, WMV, FLV, and WEBM depending
  on local multimedia support.
- Video import extracts frames for annotation in the main canvas workflow. For
  clip-level action recognition and segment labels, use the Video Classifier
  workflow below.

### Output directory behavior

- Default label location: beside each image as `<image_stem>.json`.
- Change labels location: `File > Change Output Directory` or startup
  `--output <directory>`.
- When labels are saved in a separate directory, top-level `imagePath` is saved
  relative from the label file directory to the image file. This is why moving
  labels without preserving relative image locations can break loading.
- If `--output some_file.json` is used while `auto_save` is true, the GUI warns
  that the single output file is ignored; per-image `<stem>.json` files are
  still used.

### Autosave and imageData

- Default config: `auto_save: true`, `store_data: false`.
- `File > Auto Save` or `--autosave` toggles automatic saving.
- `File > Save With Image Data` toggles base64 embedding into top-level
  `imageData`.
- Prefer `imageData: null` for normal datasets. Base64 embedding makes label
  files self-contained but can greatly increase repository size and slow review.
- On save, rectangle points are normalized to four corners. Legacy two-point
  rectangles can be loaded but are converted when saved.

## 3. Main canvas tools

### Creation shortcuts and semantics

| Shape | Shortcut | Stored semantics |
|---|---:|---|
| `rectangle` | `R` | Axis-aligned box; saved as four corner points. |
| `rotation` | `O` | Rotated rectangle; four points plus optional `direction` angle metadata. Fine adjust selected shape with `Z`, `X`, `C`, `V`. |
| `polygon` | `P` | Closed polygon. Click vertices; finish by clicking the start vertex or double-clicking the last vertex. Brush polygon and magic wand also store polygons. |
| `quadrilateral` | `T` | Four ordered corners. The first edge is displayed with an order arrow when selected. |
| `point` | `Shift+P` | Single keypoint. Use `group_id` to associate keypoints with boxes/poses/tracks. |
| `line` | `Shift+L` | Two-point segment; hold `Shift` while drawing to snap horizontal/vertical. |
| `linestrip` | `Shift+S` | Open polyline; double-click to finish. Hold `Shift` while drawing to snap segment direction. |
| `circle` | `Shift+C` | Center point plus perimeter point/radius. |
| `cuboid` | `Ctrl+R` | Front rectangle plus generated rear face; stored as eight vertices and `cuboid3d` metadata when depth data is present. |
| brush polygon | `Ctrl+N` | Assisted boundary tracing that creates a polygon. |
| magic wand | `Shift+W` | Connected color-region preview. Drag to change tolerance; right-click confirms as a polygon; `Esc` cancels. |

### Editing mode

- Toggle Drawing/Edit mode: `Ctrl+J`.
- Common operations: undo `Ctrl+Z`, copy `Ctrl+C`, paste `Ctrl+V`, duplicate
  `Ctrl+D`, delete `Delete`, move with arrow keys, and copy coordinates from
  the right-click context menu.
- Double-clicking a shape in Edit Mode opens the label editor by default. This
  can be disabled through the `canvas.double_click_edit_label` setting.
- Hold `Space` and drag to pan while drawing on a zoomed canvas.

### Shape-specific editing details

- **Rectangles**: drag corner handles; optionally use wheel rectangle editing
  when enabled. Wheel rectangle editing is disabled automatically when hover
  auto-highlight is enabled.
- **Polygons/linestrips**: drag an edge to insert a vertex; hold `Shift` and
  click a vertex to remove it. With one polygon/linestrip selected, `Alt` enters
  eraser mode. `Shift+B` edits a selected polygon with a brush; right-click or
  turn off brush edit to commit, `Esc`/image switch/tool switch discards.
- **Rotated rectangles**: drag the rotation handle for coarse rotation; use
  `Z`/`V` for larger angle steps and `X`/`C` for smaller steps.
- **Cuboids**: edit mode shows front vertices, front edge centers, visible rear
  vertices, and a rear depth handle. Dragging front face moves the cuboid;
  dragging rear controls changes depth and plane alignment.
- **Locked shapes**: remain selectable and allow label/attribute edits, but
  geometry changes and deletion are disabled. Unlock before geometry repair.

### Labels, attributes, descriptions, and links

- Shape label entry supports fuzzy search unless exact validation is enabled.
- `group_id` groups related shapes: use it for pose boxes/keypoints, tracking
  identities, and any multi-shape object that must stay associated downstream.
- `difficult` marks hard objects and is searchable.
- Shape `description` is instance-level text; the right-panel image description
  (when no shape is selected) is top-level JSON `description`.
- Shape `attributes` are stored as a dictionary. Supported uploaded widget
  styles include text fields, radio/check options, combo boxes, and group-id
  selectors when configured correctly.
- `kie_linking` links shapes for key information extraction; it must be a list
  of integer pairs.

## 4. Review and search workflows

### Checked status

- Toggle current annotation checked: right-click canvas and choose Mark as
  Checked/Unchecked, or press `Ctrl+Alt+K`.
- Next unchecked: `Ctrl+Shift+D`; previous unchecked: `Ctrl+Shift+A`.
- The file list status dot is green for checked and gray for unchecked.
- File-list checkboxes indicate whether a label file exists; they are distinct
  from the annotation checked-status dot. Checkbox editability is configurable.

### File and object search

The file search box supports:

- Plain text: matches filenames containing the text.
- Index search: `#10` jumps to the tenth item in the current list.
- Regex search: `<\.png$>` finds PNG files.
- Attribute search:
  - `difficult::1` or `difficult::true`
  - `gid::0`
  - `shape::1` / `shape::true`
  - `label::person`
  - `type::rectangle` (also polygon, rotation, quadrilateral, point, line,
    circle, linestrip)
  - `score::[0,0.5]`, `score::(0,0.6]`, `score::[0,0.6)`, `score::(0,0.6)`
  - `description::1` / `description::true`
  - `checked::1` / `checked::true`
  - `checked::0` / `checked::false`; images without label files count as
    unchecked.

### Review helpers

- `Ctrl+Shift+N`: loop through objects and zoom in for inspection.
- `Ctrl+Shift+C`: loop-select objects.
- `Ctrl+H`: show/hide all shapes.
- `Ctrl+L`: show/hide labels.
- `Ctrl+T`: show/hide descriptions.
- `Ctrl+K`: show/hide KIE links.
- `Ctrl+Shift+L`: show/hide attributes.
- `Ctrl+M`: show/hide masks.
- `Alt+L`: Label Manager for rename/delete/visibility/color in the selected
  dataset range.
- `Alt+G`: Group ID Manager for batch group-id changes/removal.
- `Alt+S`: Shape Manager for frame-sequence operations: delete annotations,
  delete images with annotations, remove selected shape across range, or add a
  selected shape across range. Deletion requires care; deleted images move to a
  `_delete_` folder while deleted labels are removed.
- `Tools > Overview`: dataset statistics by label and shape type, with optional
  CSV/ZIP report export.

## 5. Classifier and multimodal UI modes

These modes are launched from the main GUI and store data in XLABEL-compatible
sidecars/fields. AI assistance inside them may require model/provider setup;
route model configuration and downloads away from this sub-skill.

### Image Classifier (`Ctrl+3`)

- Requires an image directory loaded in the main window.
- Supports MultiClass (exactly one active label per image) and MultiLabel
  (multiple active labels per image).
- Image-classification annotations are stored in top-level `flags`:

  ```json
  {
    "flags": {"husky": true, "psyduck": false},
    "shapes": [],
    "imagePath": "sample.png",
    "imageData": null,
    "imageHeight": 200,
    "imageWidth": 200,
    "description": ""
  }
  ```

- Labels can be added manually or imported from a one-label-per-line text file.
  Label names must be unique.
- Deleting labels removes those flags across label files. Renaming labels updates
  stored flag keys.
- Switching from MultiLabel to MultiClass keeps only the first selected label
  per image.
- Export organizes images into category-specific folders in MultiClass mode.

### Video Classifier (`Ctrl+5`)

- Loads videos by drag/drop or open-video control. Common extensions include
  MP4, MOV, MKV, AVI, WEBM, M4V, FLV, and WMV.
- Label setup controls classes and colors. The first ten labels can be selected
  with numeric keys `0`–`9`.
- Create segments by right-dragging the timeline ruler, or mark `I`/`O` and
  press `Enter`. Edit by dragging, resizing edges, double-clicking labels, or
  using Delete/Backspace. Save sidecar with `Ctrl+S`.
- Stored sidecar file is beside the video with the same stem and `.json`:

  ```json
  {
    "version": "1.0.0",
    "type": "video_classification",
    "video": "sample.mp4",
    "fps": 30.0,
    "duration_ms": 120000,
    "width": 1920,
    "height": 1080,
    "labels": ["run", "walk"],
    "label_colors": {"run": "#ff7f0e", "walk": "#1f77b4"},
    "segments": [
      {
        "id": "s1234567890",
        "label": "run",
        "start_ms": 1000,
        "end_ms": 3500,
        "start_frame": 30,
        "end_frame": 105,
        "description": "The person starts running after the whistle."
      }
    ]
  }
  ```

- Dataset export can write video clips and/or raw frame sequences organized by
  label. Clip export needs an available `ffmpeg` executable or `imageio-ffmpeg`.

### VQA (`Ctrl+2`)

- Requires an image directory loaded in the main window.
- Component configuration is stored under the selected work dir in
  `xanylabeling_data/vqa/components.json`.
- Supported component types: text input, radio buttons, checkboxes, and dropdown
  menu.
- Values are autosaved under top-level `vqaData` in each image label JSON:

  ```json
  {
    "flags": {},
    "shapes": [],
    "vqaData": {
      "question": "How many zebras are there?",
      "answer": 3,
      "split": "train",
      "task": "Counting",
      "tags": ["natural"]
    },
    "imagePath": "000000000154.jpg",
    "imageData": null,
    "imageHeight": 640,
    "imageWidth": 480
  }
  ```

- Prompt reference tokens inside AI-assisted fields include `@image`, `@text`,
  `@widget.<component_name>`, `@label.shapes`, `@label.imagePath`,
  `@label.imageHeight`, `@label.imageWidth`, and `@label.flags`.
- Export Labels writes JSONL with selected basic fields and component fields.

### Chatbot (`Ctrl+1`)

- Stores per-image conversations under top-level `chat_history`:

  ```json
  {
    "chat_history": [
      {"role": "user", "content": "<image> Describe this image.", "image": "sample.jpg"},
      {"role": "assistant", "content": "A dog on grass.", "image": null}
    ]
  }
  ```

- The special `@image` prompt token is stored as `<image>` in chat history and
  links the current image to the user message.
- Batch image processing applies one prompt to a loaded image directory and
  writes chat history into each image's label JSON.
- Dataset export can produce multimodal ShareGPT-style archives; ensure image
  paths referenced by label JSON are still valid before export.
