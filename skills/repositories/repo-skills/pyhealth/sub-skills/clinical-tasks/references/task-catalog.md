# Task catalog and selection

Select by clinical question and data source, not by model name:

- **Mortality:** in-hospital or longitudinal mortality tasks for MIMIC/eICU/MEDS.
- **Readmission:** patient revisit/readmission tasks for MIMIC, eICU, or OMOP.
- **Length of stay/survival:** continuous, bucketed, or time-to-event targets;
  inspect censoring and time origin.
- **Drug recommendation:** diagnoses/procedures/history to medication labels;
  route multilabel and DDI metrics to evaluation.
- **Clinical coding:** ICD coding or medical-transcription classification;
  distinguish code target vocabulary from feature mapping.
- **Imaging/physiology:** CXR, EEG, sleep staging, cardiology, and signal tasks;
  validate modality processors before model selection.
- **NLP/de-identification:** text classification, NER/de-identification, and
  text generation; model weights/corpora may be external.
- **Genomics/variant/linkage:** ClinVar, TCGA, patient-linkage/MedLink; verify
  local resources and privacy before constructing a cohort.

Use the current `pyhealth.tasks` exports and API pages to choose a class. The
repository's examples include useful intent but some use old 1.x names such as
`DrugRecDataset`, `MIMIC3BaseDataset`, `MLModel`, or `evaluator`; treat those as
historical evidence and translate them to current dataset/task/model/Trainer
contracts.
