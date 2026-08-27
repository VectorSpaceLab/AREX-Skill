#!/usr/bin/env python3
"""Smoke-test TorchDrug Configurable round-trips without datasets or training."""

from torchdrug import core, models


def main():
    input_dim = 64
    hidden_dims = [64, 64]
    num_mlp_layer = 3

    model = models.GIN(input_dim, hidden_dims)
    infograph = models.InfoGraph(model, num_mlp_layer)

    config = infograph.config_dict()
    loaded = core.Configurable.load_config_dict(config)
    loaded_config = loaded.config_dict()

    if config != loaded_config:
        raise AssertionError("Configurable round-trip changed the InfoGraph config")

    print("TorchDrug Configurable round-trip OK")
    print("class=%s" % loaded_config["class"])
    print("encoder=%s" % loaded_config["model"]["class"])


if __name__ == "__main__":
    main()
