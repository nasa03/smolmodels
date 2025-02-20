"""
This module provides the Dataset class, which represents a collection of data that can be real,
synthetic, or a combination of both.

The Dataset class offers functionalities for:
- Wrapping existing datasets (e.g. pandas DataFrames).
- Generating synthetic data based on a schema.
- Augmenting real datasets with additional synthetic samples.
- Iterating and accessing data samples conveniently.

Users can either pass raw datasets directly to models or leverage this class for dataset management and augmentation.
"""

from typing import Iterator
import pandas as pd
from smolmodels.internal.common.provider import Provider
from smolmodels.internal.common.datasets.adapter import DatasetAdapter
from smolmodels.internal.schemas.resolver import SchemaResolver
from smolmodels.internal.datasets.generator import DatasetGenerator as DataGenerator


class DatasetGenerator:
    """
    Represents a dataset, which can contain real data, synthetic data, or both.

    This class provides a structured way to manage data, allowing users to:
    - Wrap real datasets (pandas etc.).
    - Generate synthetic data from scratch.
    - Augment existing datasets with synthetic samples.

    Example:
        >>> synthetic_dataset = DatasetGenerator(
        >>>     description="Synthetic reviews",
        >>>     provider="openai/gpt-4",
        >>>     schema=MovieReviewSchema,
        >>>     num_samples=100
        >>> )
        >>> model.build(datasets={"train": synthetic_dataset})
    """

    def __init__(
        self,
        description: str,
        provider: str,
        schema: dict = None,
        data: pd.DataFrame = None,
    ) -> None:
        """
        :param description: A human-readable description of the dataset
        :param provider: LLM provider used for synthetic data generation
        :param schema: The schema the data should match, if any
        :param data: A dataset of real data on which to base the generation, if available
        """
        # Core attributes required for dataset generation
        self.description = description
        self.provider = Provider(provider)

        # Internal attributes for data management
        self._data: pd.DataFrame = data
        self._index = 0

        if schema is not None and data is not None:
            self.schema = schema
            self._validate_schema(data)
            self._data = DatasetAdapter.coerce(data)
        elif data is not None:
            self._data = DatasetAdapter.coerce(data)
            schemas = SchemaResolver(self.provider, self.description).resolve({"data": self._data})
            self.schema = {**schemas[0], **schemas[1]}
        elif schema is not None:
            self.schema = schema

        self.data_generator = DataGenerator(self.provider, self.description, self.schema)

    def generate(self, num_samples: int):
        """Generates synthetic data if a provider is available."""
        self._data = pd.concat([self._data, self.data_generator.generate(num_samples, self._data)], ignore_index=True)

    def _validate_schema(self, data: pd.DataFrame):
        """Ensures data matches the schema."""
        for key in self.schema.keys():
            if key not in data.columns:
                raise ValueError(f"Dataset does not match schema, missing column in dataset: {key}")

    @property
    def data(self) -> pd.DataFrame:
        """Returns the dataset."""
        if self._data is None:
            raise ValueError("No data has been set or generated.")
        return self._data

    def __len__(self) -> int:
        """Returns the number of samples in the dataset."""
        if isinstance(self._data, pd.DataFrame):
            return len(self._data)
        return 0

    def __iter__(self) -> Iterator:
        """Returns an iterator over the dataset."""
        self._index = 0
        return self

    def __next__(self):
        """Returns the next item in the dataset."""
        if self._data is None or self._index >= len(self):
            raise StopIteration

        if isinstance(self._data, pd.DataFrame):
            row = self._data.iloc[self._index].to_dict()
        else:
            raise TypeError("Unsupported data type in dataset.")

        self._index += 1
        return row

    def __getitem__(self, index: int):
        """Returns the dataset item at a given index."""
        if self._data is None:
            raise IndexError("Dataset is empty.")

        if isinstance(self._data, pd.DataFrame):
            return self._data.iloc[index].to_dict()
        else:
            raise TypeError("Unsupported data type in dataset.")
