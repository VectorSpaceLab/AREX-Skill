# Project, label, and annotation workflows

doccano uses a project-centric model. A project defines the task type, labels, members, and collaborative settings that control how examples are annotated.

## Create the project

1. Create a project from the project list page.
2. Choose the task type that matches the data and annotation shape.
3. Fill in the description and guideline fields as needed.
4. Decide whether the project is collaborative, whether classification is single-class, and whether overlapping spans are allowed.

## Define labels

- Document classification uses category labels.
- Sequence labeling uses span labels and optionally relation labels.
- Seq2seq uses text labels.
- Intent detection combines categories and spans.
- Image, audio, and region-based tasks use the project-specific label type or file-based workflow.

Labels can be created manually or imported. If `allow_member_to_create_label_type` is enabled, project members can create labels too.

## Add members

- Every project has an administrator, annotator, and approver role model.
- Only project admins can add or remove members.
- Members must belong to the project before they can annotate.
- Do not remove or demote the last project admin.

## Annotate examples

- The example list is where documents or files are assigned and reviewed.
- Project admins can create examples.
- Assignment workflows can distribute examples by member weights or strategy.
- Comments are attached to examples and are visible in the example/comment workflow.

## Review progress

- Member progress shows how much each user has completed.
- Label distribution helps confirm that the expected labels were used.
- Collaborative annotation changes whether all member annotations are visible together or kept per user.

## Clone projects

Cloning duplicates the project with its role mappings, tags, examples, and label types. Use it when you want a new project with the same setup and data skeleton.

## UI route map

| Workflow | Common page |
| --- | --- |
| Project list and create | `projects/` and `projects/create` |
| Project home | `projects/<id>/` |
| Dataset | `projects/<id>/dataset/` |
| Labels | `projects/<id>/labels/` |
| Members | `projects/<id>/members/` |
| Metrics | `projects/<id>/metrics/` |
| Settings | `projects/<id>/settings/` |
| Text classification | `projects/<id>/text-classification/` |
| Sequence labeling | `projects/<id>/sequence-labeling/` |
| Seq2seq | `projects/<id>/sequence-to-sequence/` |
| Intent detection | `projects/<id>/intent-detection-and-slot-filling/` |
| Image classification | `projects/<id>/image-classification/` |
| Bounding box | `projects/<id>/object-detection/` |
| Segmentation | `projects/<id>/segmentation/` |
| Image captioning | `projects/<id>/image-captioning/` |
| Speech to text | `projects/<id>/speech-to-text/` |

## Read alongside

- `../../references/task-types.md` for the label and annotation shape of each task type.
- `../../references/cli-reference.md` when the task involves bootstrapping a new local project or user.
