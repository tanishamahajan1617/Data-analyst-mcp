from pathlib import Path
from typing import Any

import pandas as pd

from app.config import CLEANED_DATA_DIR
from app.datasets.loader import DatasetLoader
from app.datasets.loader import (
    DatasetLoader,
    DatasetStageNotFoundError,
)

class CleaningExecutionError(Exception):
    pass


class CleaningExecutor:
    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def execute(
        self,
        dataset_id: str,
        operations: list[dict[str, Any]],
    ) -> dict[str, Any]:

        # Cleaning should start from repaired if available,
        # otherwise raw. Never start from an existing cleaned copy.
        source_stage = self._get_source_stage(dataset_id)

        df = self.loader.load(
            dataset_id,
            stage=source_stage,
        )

        rows_before = len(df)

        applied_operations = []

        for operation in operations:
            df = self._apply_operation(
                df,
                operation,
            )

            applied_operations.append(operation)

        destination = self._save_cleaned_dataset(
            dataset_id,
            df,
        )

        return {
            "dataset_id": dataset_id,
            "status": "cleaned",
            "source_stage": source_stage,
            "rows_before": rows_before,
            "rows_after": len(df),
            "operations_applied": len(applied_operations),
            "cleaned_path": str(destination),
        }

    def _get_source_stage(
    self,
    dataset_id: str,
) -> str:

            if self._stage_exists(
                dataset_id,
                "repaired",
            ):
                return "repaired"

            return "raw"

    def _stage_exists(
            self,
            dataset_id: str,
            stage: str,
        ) -> bool:

            try:
                self.loader.get_path(
                    dataset_id,
                    stage=stage,
                )

                return True

            except DatasetStageNotFoundError:
                return False

    def _apply_operation(
        self,
        df: pd.DataFrame,
        operation: dict[str, Any],
    ) -> pd.DataFrame:

        operation_type = operation.get("type")

        if operation_type == "rename_column":
            return self._rename_column(
                df,
                operation,
            )

        if operation_type == "remove_duplicates":
            return df.drop_duplicates().copy()

        if operation_type == "trim_whitespace":
            return self._trim_whitespace(
                df,
                operation,
            )

        if operation_type == "convert_numeric":
            return self._convert_numeric(
                df,
                operation,
            )

        if operation_type == "handle_missing_values":
            return self._handle_missing_values(
                df,
                operation,
            )

        raise CleaningExecutionError(
            f"Unsupported cleaning operation: "
            f"{operation_type}"
        )

    def _rename_column(
        self,
        df: pd.DataFrame,
        operation: dict[str, Any],
    ) -> pd.DataFrame:

        column = operation.get("column")
        new_name = operation.get("new_name")

        if column not in df.columns:
            raise CleaningExecutionError(
                f"Column '{column}' does not exist."
            )

        if not new_name:
            raise CleaningExecutionError(
                "rename_column requires 'new_name'."
            )

        return df.rename(
            columns={
                column: new_name,
            }
        )

    def _trim_whitespace(
        self,
        df: pd.DataFrame,
        operation: dict[str, Any],
    ) -> pd.DataFrame:

        column = operation.get("column")

        self._validate_column(
            df,
            column,
        )

        df = df.copy()

        df[column] = df[column].apply(
            lambda value: (
                value.strip()
                if isinstance(value, str)
                else value
            )
        )

        return df

    def _convert_numeric(
        self,
        df: pd.DataFrame,
        operation: dict[str, Any],
    ) -> pd.DataFrame:

        column = operation.get("column")

        self._validate_column(
            df,
            column,
        )

        errors = operation.get(
            "errors",
            "coerce",
        )

        if errors not in {"raise", "coerce"}:
            raise CleaningExecutionError(
                "convert_numeric 'errors' must be "
                "'raise' or 'coerce'."
            )

        df = df.copy()

        df[column] = pd.to_numeric(
            df[column],
            errors=errors,
        )

        return df

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        operation: dict[str, Any],
    ) -> pd.DataFrame:

        column = operation.get("column")
        strategy = operation.get("strategy")

        self._validate_column(
            df,
            column,
        )

        if strategy == "drop_rows":
            return df.dropna(
                subset=[column]
            ).copy()

        df = df.copy()

        if strategy == "mean":
            value = pd.to_numeric(
                df[column],
                errors="coerce",
            ).mean()

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            ).fillna(value)

            return df

        if strategy == "median":
            numeric_series = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            value = numeric_series.median()

            df[column] = numeric_series.fillna(
                value
            )

            return df

        if strategy == "mode":
            mode = df[column].mode(
                dropna=True
            )

            if mode.empty:
                raise CleaningExecutionError(
                    f"Cannot calculate mode for '{column}'."
                )

            df[column] = df[column].fillna(
                mode.iloc[0]
            )

            return df

        if strategy == "constant":
            if "value" not in operation:
                raise CleaningExecutionError(
                    "constant strategy requires 'value'."
                )

            df[column] = df[column].fillna(
                operation["value"]
            )

            return df

        raise CleaningExecutionError(
            f"Unsupported missing-value strategy: "
            f"{strategy}"
        )

    @staticmethod
    def _validate_column(
        df: pd.DataFrame,
        column: str | None,
    ) -> None:

        if not column:
            raise CleaningExecutionError(
                "Operation requires a column."
            )

        if column not in df.columns:
            raise CleaningExecutionError(
                f"Column '{column}' does not exist."
            )

    def _save_cleaned_dataset(
        self,
        dataset_id: str,
        df: pd.DataFrame,
    ) -> Path:

        metadata = self.loader.get_metadata(
            dataset_id
        )

        filename = metadata["filename"]
        file_type = metadata["file_type"]

        directory = (
            CLEANED_DATA_DIR / dataset_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = directory / filename

        if file_type == "csv":
            df.to_csv(
                destination,
                index=False,
            )

        elif file_type == "xlsx":
            df.to_excel(
                destination,
                index=False,
            )

        else:
            raise CleaningExecutionError(
                f"Unsupported file type: {file_type}"
            )

        return destination