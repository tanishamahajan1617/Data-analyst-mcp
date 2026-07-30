from typing import Any

import pandas as pd

from app.datasets.loader import DatasetLoader


class CleaningPlanner:
    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def create_plan(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        operations: list[dict[str, Any]] = []

        self._plan_column_name_cleaning(
            df,
            operations,
        )

        self._plan_duplicate_removal(
            df,
            operations,
        )

        self._plan_missing_values(
            df,
            operations,
        )

        self._plan_string_cleaning(
            df,
            operations,
        )

        self._plan_numeric_conversion(
            df,
            operations,
        )

        return {
            "dataset_id": dataset_id,
            "source_stage": self.loader.get_active_stage(
                dataset_id
            ),
            "operation_count": len(operations),
            "operations": operations,
        }

    def _plan_column_name_cleaning(
        self,
        df: pd.DataFrame,
        operations: list[dict[str, Any]],
    ) -> None:

        for column in df.columns:
            original = str(column)
            cleaned = original.strip()

            if cleaned != original:
                operations.append(
                    {
                        "type": "rename_column",
                        "column": original,
                        "new_name": cleaned,
                        "reason": "Column name contains surrounding whitespace.",
                    }
                )

    def _plan_duplicate_removal(
        self,
        df: pd.DataFrame,
        operations: list[dict[str, Any]],
    ) -> None:

        duplicate_count = int(
            df.duplicated().sum()
        )

        if duplicate_count > 0:
            operations.append(
                {
                    "type": "remove_duplicates",
                    "count": duplicate_count,
                    "reason": (
                        f"Dataset contains {duplicate_count} "
                        "duplicate rows."
                    ),
                }
            )

    def _plan_missing_values(
        self,
        df: pd.DataFrame,
        operations: list[dict[str, Any]],
    ) -> None:

        for column in df.columns:
            missing_count = int(
                df[column].isna().sum()
            )

            if missing_count == 0:
                continue

            operations.append(
                {
                    "type": "handle_missing_values",
                    "column": str(column),
                    "count": missing_count,
                    "strategy": "review",
                    "reason": (
                        f"Column contains {missing_count} "
                        "missing values."
                    ),
                }
            )

    def _plan_string_cleaning(
        self,
        df: pd.DataFrame,
        operations: list[dict[str, Any]],
    ) -> None:

        string_columns = df.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in string_columns:
            series = df[column].dropna().astype(str)

            whitespace_count = int(
                (
                    series
                    != series.str.strip()
                ).sum()
            )

            if whitespace_count > 0:
                operations.append(
                    {
                        "type": "trim_whitespace",
                        "column": str(column),
                        "count": whitespace_count,
                        "reason": (
                            "Values contain surrounding whitespace."
                        ),
                    }
                )

    def _plan_numeric_conversion(
        self,
        df: pd.DataFrame,
        operations: list[dict[str, Any]],
    ) -> None:

        object_columns = df.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in object_columns:
            series = df[column].dropna()

            if series.empty:
                continue

            converted = pd.to_numeric(
                series,
                errors="coerce",
            )

            valid_numeric_count = int(
                converted.notna().sum()
            )

            ratio = (
                valid_numeric_count / len(series)
            )

            if 0.7 <= ratio < 1:
                invalid_count = (
                    len(series)
                    - valid_numeric_count
                )

                operations.append(
                    {
                        "type": "convert_numeric",
                        "column": str(column),
                        "numeric_ratio": round(
                            ratio,
                            2,
                        ),
                        "invalid_count": invalid_count,
                        "strategy": "review",
                        "reason": (
                            "Most values appear numeric, "
                            "but some values cannot be converted."
                        ),
                    }
                )