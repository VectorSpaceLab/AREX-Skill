# ControlNet and Annotation Maps

## Purpose

Read this when a Dream Textures scene workflow uses ControlNet, Depth/Normal/OpenPose/ADE20K/Viewport annotation maps, collection-scoped scene inputs, or a render-engine node tree that combines scene annotations with Stable Diffusion.

## Two ControlNet surfaces

Dream Textures has two scene-adjacent ControlNet surfaces:

1. **Projection panel Use ControlNet**: Project Dream Texture can use a depth ControlNet instead of a depth-to-image model. The operator renders the viewport depth map, converts it to a ControlNet image, and sends it as the first ControlNet while the generation task remains Prompt-to-Image.
2. **Dream Textures render-engine nodes**: The render engine exposes a **ControlNet** node that can either use an explicit image or render a scene/collection annotation map, then feed the result into the **Stable Diffusion** node's ControlNets input.

Image-only ControlNet preprocessing from the Image Editor belongs to `generation-workflows`; scene-derived ControlNet maps belong here.

## ControlNet node contract

The render-engine **ControlNet** node has these key properties and inputs:

| Field | Values / meaning |
| --- | --- |
| ControlNet model | Selected from the active backend's `list_controlnet_models`. It must match the conditioning map type. |
| Input Type | `Image` uses a supplied image input; `Collection` renders a scene annotation for a collection. |
| Control Type | `Depth`, `OpenPose`, `Normal Map`, or `ADE20K Segmentation` when Input Type is Collection. |
| Conditioning Scale | Strength of the ControlNet influence; default is `1`. |
| Output | A ControlNet socket carrying model id, generated/supplied image, collection, control type, and conditioning scale. |

A Stable Diffusion node accepts a single ControlNet node or a list of multiple ControlNet outputs. The node executor passes multiple links to one socket as a list.

## Annotation nodes

The render engine registers annotation nodes under the **Annotations** category. They render scene-derived images from the whole scene or from a linked Collection input.

| Node | Output | Source selection | Main prerequisites | Typical use |
| --- | --- | --- | --- | --- |
| Depth Map | `Depth Map` color socket | Scene or Collection | Camera, visible mesh/depsgraph, GPU offscreen context. | Depth-to-Image input or depth ControlNet. |
| Normal Map | `Normal Map` color socket | Scene or Collection | Camera, visible mesh, GPU offscreen context. | Normal ControlNet or diagnostic map. |
| OpenPose Map | `OpenPose Map` color socket | Scene or Collection | Camera, armature/pose objects, OpenPose bone mapping or recognizable bone names. | OpenPose ControlNet for character pose guidance. |
| ADE20K Segmentation Map | `Segmentation Map` color socket | Scene or Collection | Camera, objects with ADE20K segmentation enabled and class assigned. | Semantic-layout ControlNet or segmentation-guided generation. |
| Viewport Color | `Viewport Color` color socket | Current viewport/screen | Active VIEW_3D area, visible viewport, GPU offscreen context. | Use existing viewport color/material preview as source image or color reference. |

Annotation nodes call `context.update(map)` during execution, so the render engine can show intermediate previews when possible.

## Depth maps

Depth annotation rendering draws scene mesh depth into a GPU offscreen buffer. Defaults:

- Width/height come from scene render resolution unless explicit values are supplied internally.
- Matrix/projection default to the scene camera. Texture projection overrides these with the current viewport view and window matrices.
- Scene mode iterates evaluated object instances; collection mode iterates objects in the selected collection.
- When inverted, nearer geometry becomes stronger after normalization and background alpha masking is applied.

Use depth maps when the prompt should follow scene geometry. For render pass **Depth** or **Color and Depth**, enable the Z pass and use a depth-capable model. For ControlNet, select a depth ControlNet model instead of a depth-to-image model.

## Normal maps

Normal annotation rendering draws mesh normals into RGB-like color space and handles smooth versus flat faces separately. It uses the camera matrix by default and can be scoped to a collection. Use Normal Map conditioning only with a ControlNet model trained for normal maps; do not substitute a depth ControlNet and expect consistent results.

## OpenPose maps

OpenPose annotation rendering turns armature pose bones into colored 2D joints and limbs. It uses the scene camera projection and supports whole-scene or collection scope.

Bone matching works in two ways:

- Explicit properties: Armature and bone panels expose OpenPose settings when the Dream Textures render engine is active. Enable bones and map each bone to an OpenPose bone and side.
- Name detection fallback: common rig names such as `Head`, `spine.003`, `shoulder.L`, `upper_arm.L`, `hand_ik.L`, `LeftThigh`, `eye.L`, and related left/right variants are recognized for common OpenPose landmarks.

If a generated OpenPose map is blank, check camera visibility, armature render visibility, enabled armature/bone OpenPose properties, and whether the rig names or manual mappings correspond to the desired joints.

## ADE20K segmentation maps

ADE20K annotation rendering fills objects with predefined class colors. It only renders objects whose Dream Textures ADE20K property is enabled and assigned a class. Object properties expose an **ADE20K Segmentation** panel when the Dream Textures render engine is active.

The class enum includes common indoor/outdoor semantic labels such as wall, building, sky, floor, tree, road, bed, windowpane, chair, car, person, table, sofa, plant, water, desk, cabinet, door, and many others. Use this for semantic-layout guidance, and match it with a segmentation/ADE20K-compatible ControlNet model.

## Viewport color maps

The Viewport Color annotation node captures the current 3D Viewport color through GPU offscreen drawing. It requires an active visible VIEW_3D area and uses the scene/view-layer/space/region context. This is useful when a node tree should use Blender material preview or viewport-rendered colors as an image source. It is not reliable in headless/background Blender contexts where no viewport region exists.

## Choosing the right conditioning map

| User goal | Recommended map/input | Model requirement | Notes |
| --- | --- | --- | --- |
| Keep generated result aligned to scene geometry | Depth Map or render-pass Depth | Depth-to-image model or depth ControlNet | Depth model for Depth-to-Image; depth ControlNet for ControlNet route. |
| Preserve rendered colors and scene layout | Color and Depth render pass or Viewport Color + Depth ControlNet | Image-to-image/depth model or matching ControlNet | Lower noise strength preserves color/composition. |
| Guide a character pose | OpenPose Map | OpenPose ControlNet | Needs visible armature/camera and mapped bones. |
| Preserve surface orientation/detail | Normal Map | Normal ControlNet | Model must be normal-map compatible. |
| Guide semantic layout | ADE20K Segmentation Map | Segmentation/ADE20K ControlNet | Enable per-object ADE20K labels. |
| Reuse an already baked control image | ControlNet node Input Type = Image | ControlNet matching that image's processor/map type | For image preprocessing questions route to `generation-workflows`. |

## Minimal node-tree recipes

### Depth ControlNet render

1. Use Dream Textures render engine.
2. Create a node tree.
3. Add **Annotation > Depth Map** with Source = Scene or a collection-linked Source.
4. Add **Pipeline > ControlNet**, choose a depth ControlNet model, Input Type = Image if linking the Depth Map output as an image or Collection/Depth when rendering directly in the ControlNet node.
5. Add **Stable Diffusion** and set task to Prompt to Image or Image to Image; link ControlNet output to ControlNets input.
6. Link Stable Diffusion Image to Group Output Image.
7. Validate Width/Height as multiples of 64 using the bundled size helper.

### OpenPose ControlNet render

1. Use Dream Textures render engine and set scene camera.
2. Ensure armature/pose objects are visible to render.
3. Use automatic rig-name detection or explicitly map armature/bone OpenPose properties.
4. Add **OpenPose Map** annotation or set a ControlNet node's collection Control Type to OpenPose.
5. Choose an OpenPose-compatible ControlNet model.
6. Link the ControlNet into Stable Diffusion.

### ADE20K semantic render

1. Use Dream Textures render engine.
2. For each object that should appear in the semantic map, enable ADE20K Segmentation and choose a class.
3. Add **ADE20K Segmentation Map** or set the ControlNet node's collection Control Type to ADE20K Segmentation.
4. Choose a segmentation/ADE20K-compatible ControlNet model.
5. Keep unlabeled objects in mind: they will not contribute to the ADE20K map.

## Validation signals

- A blank depth/normal/ADE20K/OpenPose map usually indicates missing camera, hidden/non-renderable objects, collection scoping that excludes the target, or GPU offscreen failure.
- OpenPose maps need pose/armature data. Ordinary mesh characters without an armature will not create joints.
- ADE20K maps need object labels enabled; unlabeled objects are skipped.
- ControlNet output must match model type. A normal map with a depth ControlNet or OpenPose map with an ADE20K ControlNet is a mismatch even if the UI accepts a model id.
