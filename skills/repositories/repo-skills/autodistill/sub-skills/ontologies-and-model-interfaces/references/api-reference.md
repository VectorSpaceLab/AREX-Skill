# Ontologies and Model Interface API Reference

Read this for verified Autodistill 0.1.29 core class signatures and responsibilities.

## Core Abstract Classes

```text
BaseModel.__init__(self, ontology: Ontology)
BaseModel.set_ontology(self, ontology: Ontology)
BaseModel.predict(self, input: Any) -> Any
BaseModel.label(self, input_folder: str, extension: str = ".jpg", output_folder: str | None = None) -> supervision.BaseDataset

TargetModel.__init__(self)
TargetModel.predict(self, input)
TargetModel.train(self)
```

`BaseModel.__init__` does not assign `self.ontology` in this snapshot; concrete subclasses should set it explicitly.

## Detection Interfaces

```text
DetectionBaseModel.__init__(self, ontology: DetectionOntology)
DetectionBaseModel.predict(self, input: str | numpy.ndarray | PIL.Image.Image) -> supervision.Detections
DetectionBaseModel.sahi_predict(self, input: str | numpy.ndarray | PIL.Image.Image) -> supervision.Detections
DetectionBaseModel.label(...) -> supervision.DetectionDataset

DetectionTargetModel.__init__(self)
DetectionTargetModel.predict(self, input: str, confidence: float = 0.5) -> supervision.Detections
DetectionTargetModel.train(self)
```

A custom detection base model normally implements `predict` only and inherits `label`/`sahi_predict`. It must return `supervision.Detections` with `class_id` indices aligned to `ontology.classes()`.

## Classification Interfaces

```text
ClassificationBaseModel.__init__(self, ontology: CaptionOntology)
ClassificationBaseModel.predict(self, input: str) -> supervision.Classifications
ClassificationBaseModel.label(self, input_folder: str, extension: str = ".jpg", output_folder: str | None = None) -> supervision.ClassificationDataset

ClassificationTargetModel.__init__(self)
ClassificationTargetModel.predict(self, input: str, confidence: float = 0.5) -> supervision.Classifications
ClassificationTargetModel.train(self)
```

Classification data writing is implemented in the base class, but plugin maturity and target compatibility vary.

## Text Classification Interfaces

```text
TextClassificationBaseModel.__init__(self, ontology: TextClassificationOntology)
TextClassificationBaseModel.predict(self, input: str) -> dict
TextClassificationBaseModel.label(self, input_jsonl: str, output_jsonl: str = "output.jsonl") -> None

TextClassificationTargetModel.__init__(self, model_name=None)
TextClassificationTargetModel.predict(self, input: str) -> dict
TextClassificationTargetModel.train(self, dataset_file, output_dir="output", epochs=5) -> None
```

`TextClassificationBaseModel.label` is a stub in the core snapshot. Require a concrete plugin or custom implementation before promising output files.

## Ontology Classes

```text
CaptionOntology.__init__(self, ontology: Dict[str, str])
DetectionOntology.prompts(self) -> List[Any]
DetectionOntology.classes(self) -> List[str]
DetectionOntology.promptToClass(self, prompt: Any) -> str
DetectionOntology.classToPrompt(self, cls: str) -> Any
```

`CaptionOntology` stores `promptMap` as a list of `(prompt, class)` tuples. `TextClassificationOntology` stores `promptMap` differently by constructor type in this snapshot; test concrete text workflows before relying on it.

## Embedding Interfaces

```text
EmbeddingModel.__init__(self, ontology: Ontology)
EmbeddingModel.set_ontology(self, ontology: Ontology)
EmbeddingModel.embed_image(self, input: Any) -> numpy.ndarray
EmbeddingModel.embed_text(self, input: Any) -> numpy.ndarray

EmbeddingOntologyImage.__init__(self, embeddingMap, cluster=1)
EmbeddingOntologyImage.process(self, model)
EmbeddingOntologyRaw.__init__(self, embeddingMap, cluster=1)
```

Embedding ontologies are useful for few-shot image/classification workflows, but verify the concrete embedding model's vector dimensions and preprocessing.

## Composition Interface

```text
ComposedDetectionModel.__init__(self, detection_model, classification_model, set_of_marks=None, set_of_marks_annotator=...)
ComposedDetectionModel.predict(self, image: str) -> supervision.Detections
```

The composed model runs a detector, crops each detected region into `temp.jpeg`, classifies the crop, and overwrites detection `class_id` values with classification results. The optional set-of-marks branch requires the classification model to expose `set_of_marks`.
