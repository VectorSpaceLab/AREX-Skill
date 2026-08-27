# Rust API Reference

## Crate purpose

The Rust `ltp` crate implements legacy CWS/POS/NER algorithms and utilities. It is separate from the neural Python `ltp_core` package.

## Cargo features

| Feature | Use |
| --- | --- |
| `serialization` | Enables `ModelSerde`, `Format`, `Codec`, and serialized model aliases such as `CWSModel`, `POSModel`, `NERModel`. |
| `parallel` | Enables rayon-based parallel support. |
| `char-type`, `cross-char`, `near-char-type` | CWS feature/rule variants used by the legacy implementation. |

Examples that load model files require `serialization`; throughput-oriented workflows usually also enable `parallel`.

## Model loading and prediction sequence

```rust
use std::fs::File;
use itertools::multizip;
use ltp::{CWSModel, POSModel, NERModel, ModelSerde, Format, Codec};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cws: CWSModel = ModelSerde::load(File::open("cws_model.bin")?, Format::AVRO(Codec::Deflate))?;
    let pos: POSModel = ModelSerde::load(File::open("pos_model.bin")?, Format::AVRO(Codec::Deflate))?;
    let ner: NERModel = ModelSerde::load(File::open("ner_model.bin")?, Format::AVRO(Codec::Deflate))?;

    let words = cws.predict("他叫汤姆去拿外衣。")?;
    let pos_tags = pos.predict(&words)?;
    let ner_tags = ner.predict((&words, &pos_tags))?;

    for (word, pos, ner) in multizip((words, pos_tags, ner_tags)) {
        println!("{}/{}/{}", word, pos, ner);
    }
    Ok(())
}
```

## Utility APIs

The crate exposes utility modules for sentence splitting, custom word hooks, entity extraction, Eisner decoding, and Viterbi post-processing. Use them directly only when your application already owns model scores/tags; otherwise prefer high-level model prediction APIs.

## Training/build APIs

The Rust source contains generic perceptron definitions and trainer builders. Training requires data files and deliberate compute choices. For Python users, prefer the `legacy-extension` trainer API reference; for Rust users, validate data/model paths before constructing long training runs.

## Model-file expectations

Rust examples assume local legacy model binaries such as `cws_model.bin`, `pos_model.bin`, and `ner_model.bin`. This skill does not provide those files. Keep the model files outside source code and pass explicit paths.
