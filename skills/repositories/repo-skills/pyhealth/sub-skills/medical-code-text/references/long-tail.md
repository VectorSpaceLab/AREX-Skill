# Long-tail and gated capabilities

- **MedLink/patient linkage:** may require external indexing/data and has privacy
  implications; use only an authorized, de-identified fixture and document
  matching thresholds.
- **Knowledge-graph embeddings:** optional training/data paths under the package
  are not baseline import checks; bound data, epochs, and device before use.
- **OpenAI/model-hub examples:** credentials, network, model revision, and cache
  are user-owned prerequisites. Never place keys in prompts, fixtures, or logs.
- **EEG/CXR/audio:** MNE/torchvision and source datasets may be available, but
  full examples can be expensive or gated. Validate processors locally first.
- **UMLS and mapping refresh:** licensing and network/cache rules can differ from
  packaged code maps. Stop when the resource is unavailable rather than using a
  guessed ontology.
