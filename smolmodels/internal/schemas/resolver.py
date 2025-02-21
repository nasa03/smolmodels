"""
Module for schema generation and handling.
"""

import json
import logging
from enum import Enum
from typing import Tuple, Dict, Type

import pandas as pd
from pydantic import BaseModel, create_model

from smolmodels.config import config
from smolmodels.internal.common.provider import Provider
from smolmodels.internal.common.datasets.adapter import DatasetAdapter
from smolmodels.internal.common.utils.pandas_utils import convert_dtype_to_python

logger = logging.getLogger(__name__)


class SchemaResolver:
    """
    A utility class for resolving input and output schemas for a given intent and dataset.
    """

    def __init__(
        self,
        provider: Provider,
        intent: str,
        input_schema: Type[BaseModel] = None,
        output_schema: Type[BaseModel] = None,
    ):
        self.provider: Provider = provider
        self.intent: str = intent
        self.input_schema: Type[BaseModel] | None = input_schema
        self.output_schema: Type[BaseModel] | None = output_schema

    def resolve(self, datasets: Dict[str, pd.DataFrame] = None) -> Tuple[Type[BaseModel], Type[BaseModel]]:
        """
        Resolve the input and output schemas for a given intent and dataset.

        :param datasets: A dictionary of dataset names and their corresponding data.
        :return: A tuple containing the input and output schemas.
        """
        if datasets:
            return self._resolve_from_datasets(datasets)
        else:
            return self._resolve_from_intent()

    def _resolve_from_datasets(self, datasets: Dict[str, pd.DataFrame]) -> Tuple[Type[BaseModel], Type[BaseModel]]:
        """
        Generate a schema from a dataset.
        :param datasets:
        :return:
        """

        try:
            feature_names = DatasetAdapter.features(datasets)

            # Infer output column
            class OutputSchema(BaseModel):
                output: Enum("Features", {feat: feat for feat in feature_names})

            # Use LLM to decide what the output should be
            output_col = json.loads(
                self.provider.query(
                    system_message=config.code_generation.prompt_schema_base.safe_substitute(),
                    user_message=config.code_generation.prompt_schema_identify_target.safe_substitute(
                        columns="\n".join(f"- {feat}" for feat in feature_names), intent=self.intent
                    ),
                    response_format=OutputSchema,
                )
            )["output"]

            # Verify output column exists
            if output_col not in feature_names:
                raise RuntimeError(f"LLM suggested non-existent feature {output_col} as target.")

            # Infer input schema
            types = {}
            for feature in feature_names:
                match feature.split("."):
                    case [dataset, column]:
                        if isinstance(datasets[dataset], pd.DataFrame):
                            types[column] = convert_dtype_to_python(datasets[dataset][column].dtype)
                        else:
                            raise ValueError(f"Dataset {dataset} has unsupported type: '{type(datasets[dataset])}'")
                    case [dataset]:
                        raise ValueError(f"Dataset {dataset} has unsupported type: '{type(datasets[dataset])}'")
                    case _:
                        raise ValueError(f"Feature name '{feature}' is not in the expected format.")

            output_col = output_col.split(".")[-1]

            # Split into input and output schemas
            input_schema = {col: types[col] for col in types if col != output_col}
            output_schema = {output_col: types[output_col]}

            return create_model("InputSchema", **input_schema), create_model("OutputSchema", **output_schema)

        except Exception as e:
            logger.error(f"Error inferring schema from data: {e}")
            raise

    def _resolve_from_intent(self) -> Tuple[Type[BaseModel], Type[BaseModel]]:
        """
        Generate a schema from an intent using the LLM.
        :return: input and output schemas
        """
        try:

            class SchemaResponse(BaseModel):
                input_schema: Dict[str, str]
                output_schema: Dict[str, str]

            response = SchemaResponse(
                **json.loads(
                    self.provider.query(
                        system_message=config.code_generation.prompt_schema_base.safe_substitute(),
                        user_message=config.code_generation.prompt_schema_generate_from_intent.safe_substitute(
                            intent=self.intent
                        ),
                        response_format=SchemaResponse,
                    )
                )
            )
            return (
                create_model("InputSchema", **response.input_schema),
                create_model("OutputSchema", **response.output_schema),
            )
        except Exception as e:
            logger.error(f"Error generating schema from intent: {e}")
            raise
