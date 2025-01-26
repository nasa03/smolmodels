# smolmodels 🤖✨

Build specialized ML models using natural language.

## What is smolmodels?

smolmodels is a Python library that lets you create machine learning models by describing what you want them to do in plain English. Instead of wrestling with model architectures and hyperparameters, you simply describe your intent, define your inputs and outputs, and let smolmodels handle the rest.

```python
from smolmodels import Model

# Create a house price predictor with just a description
model = Model(
    intent="Predict house prices based on property features",
    input_schema={
        "square_feet": float,
        "bedrooms": int,
        "location": str,
        "year_built": int
    },
    output_schema={
        "predicted_price": float
    }
)

# Build the model - optionally generate synthetic training data
model.build("house-prices.csv", generate_samples=1000)

# Make predictions
price = model.predict({
    "square_feet": 2500,
    "bedrooms": 4,
    "location": "San Francisco",
    "year_built": 1985
})
```

## How Does It Work?

smolmodels uses a multi-step process for model creation:

1. **Intent Analysis**: Problem description is analyzed to understand the type of model needed, key requirements, and success criteria.

2. **Data Generation**:  Smolmodels can generate synthetic data to enable model build when there is no training data available.

3. **Model Building**: The library:
   - Selects appropriate model architectures
   - Handles feature engineering
   - Manages training and validation
   - Ensures outputs meets the specified constraints

4. **Validation & Refinement**: The model is tested against constraints and refined using directives (like "optimize for speed" or "prioritize explainability").

## Key Features

### Natural Language Intent 📝
Models are defined through natural language descriptions and schema specifications, abstracting away architecture decisions.

### Data Generation 🎲
Built-in synthetic data generation for training and validation.

### Directives for fine-grained Control 🎯
Guide the model building process with high-level directives:
```python
from smolmodels import Directive

model.build(directives=[
    Directive("Optimize for inference speed"),
    Directive("Prioritize interpretability")
])
```

### Optional Constraints ✅
Optional declarative constraints for model validation:
```python
from smolmodels import Constraint

# Ensure predictions are always positive
positive_constraint = Constraint(
    lambda inputs, outputs: outputs["predicted_price"] > 0,
    description="Predictions must be positive"
)

model = Model(
    intent="Predict house prices...",
    constraints=[positive_constraint],
    ...
)
```

## Installation

```bash
pip install smolmodels
```

## Quick Start

1. **Define your model**:
```python
from smolmodels import Model

model = Model(
    intent="Classify customer feedback as positive, negative, or neutral",
    input_schema={"text": str},
    output_schema={"sentiment": str}
)
```

2. **Build it**:
```python
# With existing data
model.build(dataset="feedback.csv")

# Or generate synthetic data
model.build(generate_samples=1000)
```

3. **Use it**:
```python
result = model.predict({"text": "Great service, highly recommend!"})
print(result["sentiment"])  # "positive"
```

## Documentation

For full documentation, visit [docs.plexe.ai](https://docs.plexe.ai).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache-2.0 License - see [LICENSE](LICENSE) for details.
