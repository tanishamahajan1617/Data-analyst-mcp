from pathlib import Path
from typing import Any

import pandas as pd
import re
from app.config import CLEANED_DATA_DIR
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
        source_stage = self._get_source_stage(
            dataset_id
        )

        df = self.loader.load(
            dataset_id,
            stage=source_stage,
        )

        rows_before = len(df)

        applied_operations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        for operation in operations:

            try:
                df = self._apply_operation(
                    df,
                    operation,
                )

                applied_operations.append(
                    operation
                )

            except CleaningExecutionError as exc:

                warnings.append(
                    {
                        "operation": operation,
                        "warning": str(exc),
                    }
                )

                # Continue with remaining operations.
                continue

        destination = self._save_cleaned_dataset(
            dataset_id,
            df,
        )

        return {
            "dataset_id": dataset_id,
            "status": (
                "cleaned"
                if not warnings
                else "cleaned_with_warnings"
            ),
            "source_stage": source_stage,
            "rows_before": rows_before,
            "rows_after": len(df),
            "operations_requested": len(
                operations
            ),
            "operations_applied": len(
                applied_operations
            ),
            "warnings": warnings,
            "cleaned_path": str(
                destination
            ),
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

        operation_type = operation.get(
            "type"
        )

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
            "Unsupported cleaning operation: "
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
                "rename_column requires "
                "'new_name'."
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

        minimum_success_rate = float(
            operation.get(
                "minimum_success_rate",
                0.70,
            )
        )

        df = df.copy()

        numeric = self._normalize_numeric_series(
            df[column],
            errors=errors,
        )

        original_non_null = (
            df[column]
            .notna()
            .sum()
        )

        converted_non_null = (
            numeric
            .notna()
            .sum()
        )

        if original_non_null == 0:
            success_rate = 1.0
        else:
            success_rate = (
                converted_non_null
                / original_non_null
            )

        if success_rate >= minimum_success_rate:
            df[column] = numeric

        return df


    def _normalize_numeric_series(
    self,
    series: pd.Series,
    errors: str = "coerce",
) -> pd.Series:

            cleaned = (
                series.astype(str)
                .str.strip()
            )

            cleaned = cleaned.replace(
                {
                    "": None,
                    "nan": None,
                    "NaN": None,
                    "N/A": None,
                    "NA": None,
                    "null": None,
                    "None": None,
                    "--": None,
                    "-": None,
                }
            )

            cleaned = cleaned.str.replace(
                ",",
                "",
                regex=False,
            )

            cleaned = cleaned.str.replace(
                "%",
                "",
                regex=False,
            )

            cleaned = cleaned.str.replace(
                r"[₹$€£]",
                "",
                regex=True,
            )

            cleaned = cleaned.str.replace(
                (
                    r"(?i)"
                    r"\b("
                    r"hours?|hrs?|hr|"
                    r"days?|"
                    r"weeks?|"
                    r"months?|"
                    r"years?|yrs?|"
                    r"kg|kgs?|"
                    r"km|kms?|"
                    r"litres?|liters?|l"
                    r")\b"
                ),
                "",
                regex=True,
            )

            cleaned = cleaned.str.replace(
                r"\s+",
                " ",
                regex=True,
            ).str.strip()

            return pd.to_numeric(
                cleaned,
                errors=errors,
            )

            

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

        df = df.copy()

        # ----------------------------------
        # Human review required.
        # Do not fail the pipeline.
        # ----------------------------------

        if strategy == "review":
            return df

        # ----------------------------------
        # Drop rows.
        # ----------------------------------

        if strategy == "drop_rows":
            return df.dropna(
                subset=[column]
            ).copy()

        # ----------------------------------
        # Mean.
        # ----------------------------------

        if strategy == "mean":

            numeric = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            df[column] = numeric.fillna(
                numeric.mean()
            )

            return df

        # ----------------------------------
        # Median.
        # ----------------------------------

        if strategy == "median":

            numeric = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            df[column] = numeric.fillna(
                numeric.median()
            )

            return df

        # ----------------------------------
        # Mode.
        # ----------------------------------

        if strategy == "mode":

            mode = df[column].mode(
                dropna=True,
            )

            if mode.empty:
                return df

            df[column] = df[column].fillna(
                mode.iloc[0]
            )

            return df

        # ----------------------------------
        # Constant.
        # ----------------------------------

        if strategy == "constant":

            value = operation.get(
                "value"
            )

            df[column] = df[column].fillna(
                value
            )

            return df

        raise CleaningExecutionError(
            "Unsupported missing-value "
            f"strategy: {strategy}"
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
                f"Column '{column}' "
                "does not exist."
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
            CLEANED_DATA_DIR
            / dataset_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            directory
            / filename
        )

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
                "Unsupported file type: "
                f"{file_type}"
            )

        return destination