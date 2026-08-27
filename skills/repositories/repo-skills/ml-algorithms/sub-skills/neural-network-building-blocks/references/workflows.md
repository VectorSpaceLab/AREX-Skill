# Neural network workflows

## Purpose

Use these recipes to build short MLAlgorithms neural-network checks and to adapt longer example patterns safely. Keep training small unless the user explicitly wants a long educational run.

## Dense regression workflow

```python
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Dense, Activation
from mla.neuralnet.optimizers import Adam
from mla.metrics.metrics import mean_squared_error

X, y = make_regression(n_samples=200, n_features=6, noise=0.05, random_state=1111)
y = y * 0.01
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1111)
model = NeuralNet(
    layers=[Dense(16), Activation("linear"), Dense(1)],
    optimizer=Adam(),
    loss="mse",
    metric="mse",
    batch_size=32,
    max_epochs=5,
    verbose=False,
)
model.fit(X_train, y_train)
pred = model.predict(X_test).flatten()
print(mean_squared_error(y_test, pred))
```

Use this pattern for smoke tests because it avoids one-hot labels and large examples.

## Dense classification workflow

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Dense, Activation, Dropout
from mla.neuralnet.optimizers import Adadelta
from mla.utils import one_hot

X, y = make_classification(n_samples=300, n_features=20, n_informative=10, n_classes=2, random_state=1111)
y = one_hot(y)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1111)
model = NeuralNet(
    layers=[Dense(32), Activation("relu"), Dropout(0.2), Dense(2), Activation("softmax")],
    loss="categorical_crossentropy",
    optimizer=Adadelta(),
    metric="accuracy",
    batch_size=32,
    max_epochs=5,
)
model.fit(X_train, y_train)
proba = model.predict(X_test)
```

For `categorical_crossentropy`, one-hot encode labels and end with `Activation("softmax")`.

## CNN pattern

Use a 4D input tensor `(batch, channels, height, width)`:

```python
from mla.neuralnet.layers import Convolution, Activation, MaxPooling, Flatten, Dense

layers = [
    Convolution(n_filters=8, filter_shape=(3, 3), padding=(1, 1)),
    Activation("relu"),
    MaxPooling(pool_shape=(2, 2), stride=(2, 2)),
    Flatten(),
    Dense(10),
    Activation("softmax"),
]
```

The repository's MNIST example is long-running; use it as an architecture pattern and prefer small synthetic tensors for smoke checks.

## RNN/LSTM pattern

Use sequence tensors shaped `(batch, timesteps, features)`:

```python
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Activation, TimeDistributedDense
from mla.neuralnet.layers.recurrent import LSTM
from mla.neuralnet.optimizers import Adam

model = NeuralNet(
    layers=[LSTM(16, return_sequences=True), TimeDistributedDense(1), Activation("sigmoid")],
    loss="mse",
    optimizer=Adam(),
    metric="mse",
    batch_size=16,
    max_epochs=3,
)
```

Use `return_sequences=False` when only the final state should flow into a dense classifier.

## DQN pattern

The DQN wrapper expects a model factory:

```python
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Dense, Activation
from mla.neuralnet.optimizers import Adam
from mla.rl.dqn import DQN

def model_factory(n_actions, batch_size=32):
    return NeuralNet(
        layers=[Dense(16), Activation("relu"), Dense(n_actions)],
        loss="mse",
        optimizer=Adam(),
        metric="mse",
        batch_size=batch_size,
        max_epochs=1,
        verbose=False,
    )

agent = DQN(n_episodes=1, batch_size=16)
# agent.init_environment("CartPole-v0")
# agent.init_model(model_factory)
```

Do not run `train` or `play` blindly in automation; read `rl-dqn.md` for Gym compatibility and render warnings.

## Safe bundled smoke

From this sub-skill directory, run:

```bash
python scripts/run_neural_smoke.py --workflow all
```

From the root `ml-algorithms` skill directory, use `python sub-skills/neural-network-building-blocks/scripts/run_neural_smoke.py --workflow all`.

The helper checks a tiny dense model, RBM compatibility, and DQN model factory wiring without long training or rendering.
