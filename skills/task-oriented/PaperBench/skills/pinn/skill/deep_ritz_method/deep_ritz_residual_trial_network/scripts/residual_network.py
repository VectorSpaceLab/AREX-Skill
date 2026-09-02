import argparse
import json


def cubic_relu_tensor(x):
    import torch
    return torch.clamp(x, min=0.0) ** 3


def estimate_parameter_count(dimension, width, blocks):
    input_layer = dimension * width + width
    block_params = blocks * (2 * (width * width + width))
    output_layer = width + 1
    return input_layer + block_params + output_layer


def build_torch_model(dimension, width=10, blocks=3):
    import torch

    class ResidualBlock(torch.nn.Module):
        def __init__(self, hidden_width):
            super().__init__()
            self.first = torch.nn.Linear(hidden_width, hidden_width)
            self.second = torch.nn.Linear(hidden_width, hidden_width)

        def forward(self, values):
            return cubic_relu_tensor(self.second(cubic_relu_tensor(self.first(values)))) + values

    class TrialNetwork(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.input_layer = torch.nn.Linear(dimension, width)
            self.blocks = torch.nn.ModuleList([ResidualBlock(width) for _ in range(blocks)])
            self.output_layer = torch.nn.Linear(width, 1)

        def forward(self, coordinates):
            values = cubic_relu_tensor(self.input_layer(coordinates))
            for block in self.blocks:
                values = block(values)
            return self.output_layer(values)

    return TrialNetwork()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimension", type=int, default=10)
    parser.add_argument("--width", type=int, default=10)
    parser.add_argument("--blocks", type=int, default=3)
    args = parser.parse_args()
    info = {
        "dimension": args.dimension,
        "width": args.width,
        "blocks": args.blocks,
        "parameter_count": estimate_parameter_count(args.dimension, args.width, args.blocks),
        "activation": "cubic_relu",
    }
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
