# CVAT overview

CVAT Community is a self-hosted computer-vision annotation platform. It supports image, video, and 3D/point-cloud annotation, task/project/job organization, collaboration, dataset import/export, cloud storage, SDK/REST/CLI automation, and optional model-assisted annotation.

## Main operating surfaces

| Surface | Package/files | Use |
|---|---|---|
| Web UI | CVAT server/UI deployment | Human annotation, review, projects/tasks/jobs, organizations, model-assisted tools. |
| Python SDK | `cvat-sdk` / `cvat_sdk` | Programmatic server automation, high-level objects, generated REST API fallback, dataset adapters, auto-annotation helpers. |
| CLI | `cvat-cli` / `cvat-cli` command | Shell automation for profiles/config, tasks, projects, imports/exports, backups, frames, auto-annotation, native functions. |
| REST API | Generated SDK API client and server schema | Low-level integration when high-level SDK/CLI does not expose a needed endpoint. |
| Dataset manager | CVAT server + SDK/CLI import/export | Conversion among CVAT XML, COCO, YOLO, Datumaro, Pascal VOC, KITTI, MOT/MOTS, and other formats. |
| Auto-annotation | `cvat_sdk.auto_annotation`, CLI function commands, serverless functions | Local models, native AI functions, and Nuclio serverless model deployment. |
| Deployment | Docker Compose, Helm chart, optional overlays | Self-hosted Community stack, serverless infrastructure, development/test services. |

## Version anchors

This skill was generated from a development checkout whose CVAT core version metadata was `2.72.1-alpha.0`, while `cvat-sdk` and `cvat-cli` package metadata reported `2.72.1`. Match SDK/CLI versions to the server version whenever possible.

## Dependencies and extras

Core automation:

```bash
pip install cvat-sdk cvat-cli
```

Optional SDK extras:

- `cvat-sdk[masks]`: mask encode/decode helpers that need NumPy.
- `cvat-sdk[pytorch]`: PyTorch dataset adapter and torchvision-based auto-annotation helpers; can be large and backend-sensitive.

Self-hosted deployment requires Docker/Compose and server-side services rather than only Python packages.

## Skill boundaries

- Root routing explains where to go; detailed recipes live in sub-skills.
- SDK/CLI sub-skills assume an existing reachable CVAT server unless a workflow explicitly creates one.
- Dataset operations choose formats and movement paths but route authentication and deployment to sibling sub-skills.
- Auto-annotation covers model/function protocols and serverless model patterns, not generic model training.
- Deployment-admin covers running/administering CVAT, not writing CVAT source code.
