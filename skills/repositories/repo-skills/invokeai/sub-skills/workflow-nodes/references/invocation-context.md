# InvocationContext

`InvocationContext` is the safe service facade passed to `BaseInvocation.invoke(self, context)`. It provides per-node access to images, tensors, conditioning, models, logging, configuration, progress/cancel utilities, boards, and workflow data without exposing the full internal services object.

Use the generated method catalog with:

```bash
python scripts/summarize_invocation_context.py
python scripts/summarize_invocation_context.py --json
python scripts/summarize_invocation_context.py path/to/invocation-context.json --interface ImagesInterface
```

The script uses the bundled distilled summary by default and accepts a full generated context JSON file when one is available.

## Context Shape

The context includes these service groups:

- `context.images`: save, load, and inspect image DTO/PIL/path/metadata data.
- `context.tensors`: save and load tensor payloads by generated name.
- `context.conditioning`: save and load conditioning data by generated name.
- `context.models`: inspect, search, download/cache, and load models through the model manager facade.
- `context.logger`: `debug`, `info`, `warning`, and `error` messages.
- `context.config`: read current app configuration.
- `context.util`: cancellation checks, progress reporting, and denoising step callbacks.
- `context.boards`: create/read boards and add/list board images.
- `context.workflow`: current workflow payload, exposed by context; do not use deprecated `WithWorkflow`.

A fresh context is built per executing node, so nodes should communicate through graph outputs and persisted service data, not by mutating context internals.

## Images

Methods:

- `get_dto(image_name: str) -> ImageDTO`: fetch image DTO metadata.
- `get_metadata(image_name: str) -> Optional[MetadataField]`: fetch saved metadata.
- `get_path(image_name: str, thumbnail: bool = False) -> Path`: fetch internal image/thumbnail path.
- `get_pil(image_name: str, mode: Optional[Literal['L', 'RGB', 'RGBA', 'CMYK', 'YCbCr', 'LAB', 'HSV', 'I', 'F']] = None) -> Image`: return a copy of a PIL image, converted when possible.
- `save(image: Image, board_id: Optional[str] = None, image_category: ImageCategory = ImageCategory.GENERAL, metadata: Optional[MetadataField] = None) -> ImageDTO`: save a PIL image and return its DTO.

`images.save()` automatically applies `WithMetadata.metadata`, `WithBoard.board`, queue workflow, graph JSON, session ID, node ID, user ID, and `is_intermediate` when available. Pass `board_id` or `metadata` only to override the mixin-provided values intentionally.

Typical pattern:

```python
image = context.images.get_pil(self.image.image_name, mode="RGBA")
# process image
image_dto = context.images.save(image=image)
return ImageOutput.build(image_dto)
```

## Tensors and Conditioning

Tensor methods:

- `save(tensor: Tensor) -> str`: persist tensor payload and return its name.
- `load(name: str) -> Tensor`: load a cloned tensor by name.

Conditioning methods:

- `save(conditioning_data: ConditioningFieldData) -> str`: persist conditioning payload and return its name.
- `load(name: str) -> ConditioningFieldData`: load a deep copy by name.

Return field references such as `LatentsField` or `ConditioningField`, not the large tensor/conditioning object itself.

## Models

Methods:

- `exists(identifier: Union[str, ModelIdentifierField]) -> bool`: test model presence by key or model field.
- `get_config(identifier: Union[str, ModelIdentifierField]) -> AnyModelConfig`: fetch config.
- `search_by_attrs(name=None, base=None, type=None, format=None) -> list[AnyModelConfig]`: search model records.
- `search_by_path(path: Path) -> list[AnyModelConfig]`: search model records by path.
- `get_absolute_path(config_or_path: Union[AnyModelConfig, Path, str]) -> Path`: resolve a configured model path.
- `load(identifier: Union[str, ModelIdentifierField], submodel_type: Optional[SubModelType] = None) -> LoadedModel`: load registered model or submodel.
- `load_by_attrs(name: str, base: BaseModelType, type: ModelType, submodel_type: Optional[SubModelType] = None) -> LoadedModel`: find a unique model by attrs and load it.
- `download_and_cache_model(source: str | AnyHttpUrl) -> Path`: download/cache a model-like resource without registering it.
- `load_local_model(model_path: Path, loader: Optional[Callable[[Path], AnyModel]] = None) -> LoadedModelWithoutConfig`: load file without a model DB config.
- `load_remote_model(source: str | AnyHttpUrl, loader: Optional[Callable[[Path], AnyModel]] = None) -> LoadedModelWithoutConfig`: download/cache and load file without a model DB config.

Model service details, taxonomy choices, and cache behavior belong in `../model-management/`. In this sub-skill, use the model methods only to understand node authoring and context access.

Caveats:

- External API models cannot be loaded from disk through `load()`/`load_by_attrs()`.
- `load_local_model()` and `load_remote_model()` return loaded models without a config attribute.
- Model-loading nodes should call `context.util.signal_progress()` indirectly through model context methods or directly for long operations.

## Logging, Config, Progress, and Boards

Logger methods:

- `debug(message: str) -> None`
- `info(message: str) -> None`
- `warning(message: str) -> None`
- `error(message: str) -> None`

Config method:

- `get() -> InvokeAIAppConfig`: read app config. Route config-file/server changes to `../operations-config/`.

Util methods:

- `is_canceled() -> bool`: check cancellation during long loops.
- `signal_progress(message: str, percentage: float | None = None, image: Image | None = None, image_size: tuple[int, int] | None = None) -> None`: emit progress.
- `sd_step_callback(intermediate_state: PipelineIntermediateState, base_model: BaseModelType) -> None`
- `flux_step_callback(intermediate_state: PipelineIntermediateState) -> None`
- `flux2_step_callback(intermediate_state: PipelineIntermediateState) -> None`

Board methods:

- `create(board_name: str) -> BoardDTO`
- `get_dto(board_id: str) -> BoardDTO`
- `get_all() -> list[BoardDTO]`
- `add_image_to_board(board_id: str, image_name: str) -> None`
- `get_all_image_names_for_board(board_id: str) -> list[str]`

## Safe Node Patterns

- Read images/tensors/conditioning through context, make local copies or use returned copies, and save new artifacts instead of mutating prior outputs.
- Return output field references and dimensions/metadata needed by downstream nodes.
- Use `WithMetadata`/`WithBoard` on image-producing nodes that should preserve workflow metadata and board routing.
- Check `context.util.is_canceled()` in loops that can run long.
- Use `context.logger.warning()` for recoverable user-facing issues such as unsupported color mode conversion.
- Keep direct filesystem access explicit and constrained. For gallery images, prefer context image methods.

## Testing Context-Using Nodes

Unit tests often use `MagicMock` context objects:

```python
context = MagicMock()
context.images.get_pil.return_value = input_image
context.images.save.side_effect = lambda image: SimpleNamespace(image_name="out", width=image.width, height=image.height)
output = invocation.invoke(context)
```

This pattern is useful for image transforms and pure node logic. Use real service-backed tests only when checking persistence, model loading, queue/session integration, or API behavior.
