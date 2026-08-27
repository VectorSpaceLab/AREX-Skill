# Troubleshooting

This guide covers the most common notebook, image, selector, and resource-view failures.

## Fast triage

If a user only sends a GPU string or selector snippet, run `scripts/parse_resource_gpu.py` first. It is the safest way to see whether the input is a CPU request, a GPU request, or an invalid string.

## Resource-string problems

Symptoms:

- GPU requests are rejected by the form
- the notebook lands on the wrong node class
- the pod has no visible GPU

What to check:

- `resource_gpu` must be a non-negative integer with an optional model in parentheses
- ASCII and Chinese parentheses are both accepted by the backend parser
- commas inside the model string are rejected
- the backend parser is stricter than some UI regexes, so trust the parser over the form hint
- if the count is zero, GPU-specific selector changes are skipped and the pod gets `NVIDIA_VISIBLE_DEVICES=none`

## Selector and placement problems

Symptoms:

- the notebook or debug pod lands on CPU nodes when GPU was requested
- the expected resource group is missing in the resource view
- the notebook selector does not include the right org label

What to check:

- project `expand.cluster` points to the intended cluster
- project `expand.org` matches the resource-group label on the nodes
- the node label set includes `cpu=true`, `gpu=true`, `notebook=true`, and any `gpu-type` label you expect to bind
- `get_default_node_selector()` automatically flips CPU labels to GPU labels when the GPU count is positive
- `org` defaults to `public` if it is missing from the selector
- if a model-specific GPU such as `V100` is requested, remember that the pod helper also adds `gpu-type=V100`

## Notebook lifecycle failures

Symptoms:

- notebook stays pending
- notebook opens to a blank page
- reset does not recreate the pod
- renew does not extend the session
- save is missing

What to check:

- image pull secret exists and matches the registry host
- `Repository.server` matches the registry part of the image name
- the namespace exists and the project has the right mounts
- `SERVICE_EXTERNAL_IP` and `NOTEBOOK_PORT` are correct in edge deployments
- `CRD_INFO.virtualservice` is present when the cluster uses a VirtualService route
- `init.sh` or `/mnt/<user>/init.sh` may be failing during startup
- `save` is only a commercial UI marker and should not be treated as a normal notebook persistence flow

## Registry and image catalog problems

Symptoms:

- the image list does not show the expected labels
- new notebook images are missing from the UI
- online debug / commit / push fails to find a repository

What to check:

- `NOTEBOOK_IMAGES` has the expected shape: list of pairs or a cascade dictionary
- `Images.image_type` is one of the supported catalog categories
- the registry host used in the target image exists in `Repository`
- the user's namespace received the `hubsecret`
- the image family belongs in this sub-skill; serving / inference image work should go to the sibling route

## Monitoring and resource-view problems

Symptoms:

- the resource page is empty
- GPU charts are blank
- Grafana links are wrong
- `dcgm-exporter` metrics are missing

What to check:

- the user belongs to the project or resource group being viewed
- Grafana path config keys are present
- NVIDIA device-plugin and `dcgm-exporter` are installed for NVIDIA GPU nodes
- vendor accelerators may need different labels or metrics and are not covered by these NVIDIA-specific dashboards
- `py_prometheus` queries the same Prometheus family that powers the resource page

## Workflow-specific reminders

- notebooks are disposable sessions; keep durable work under `/mnt/<user>` or in Git
- changing notebook images or mounts usually needs a reset
- online image builds belong to the image catalog workflow, not the notebook workflow
- platform installation and GPU plugin deployment belong to the deploy sub-skill
