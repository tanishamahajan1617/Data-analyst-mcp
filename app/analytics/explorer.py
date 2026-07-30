from typing import Any

import pandas as pd

from app.datasets.loader import DatasetLoader


class ExplorationError(Exception):
    pass


class DatasetExplorer:
    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def summary(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        numeric_columns = list(
            df.select_dtypes(include="number").columns
        )

        categorical_columns = list(
            df.select_dtypes(
                include=["object", "string", "category"]
            ).columns
        )

        return {
            "dataset_id": dataset_id,
            "stage": self.loader.get_active_stage(dataset_id),
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "numeric_columns": [
                str(column)
                for column in numeric_columns
            ],
            "categorical_columns": [
                str(column)
                for column in categorical_columns
            ],
        }

    def numeric_statistics(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        numeric_df = df.select_dtypes(
            include="number"
        )

        if numeric_df.empty:
            return {
                "dataset_id": dataset_id,
                "columns": {},
            }

        results = {}

        for column in numeric_df.columns:
            series = numeric_df[column].dropna()

            if series.empty:
                continue

            results[str(column)] = {
                "count": int(series.count()),
                "mean": self._number(series.mean()),
                "median": self._number(series.median()),
                "std": self._number(series.std()),
                "min": self._number(series.min()),
                "max": self._number(series.max()),
                "q1": self._number(series.quantile(0.25)),
                "q3": self._number(series.quantile(0.75)),
            }

        return {
            "dataset_id": dataset_id,
            "columns": results,
        }

    def value_counts(
        self,
        dataset_id: str,
        column: str,
        limit: int = 10,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        self._validate_column(df, column)

        if limit < 1 or limit > 100:
            raise ExplorationError(
                "limit must be between 1 and 100."
            )

        counts = (
            df[column]
            .value_counts(dropna=False)
            .head(limit)
        )

        values = []

        for value, count in counts.items():
            values.append(
                {
                    "value": (
                        None
                        if pd.isna(value)
                        else str(value)
                    ),
                    "count": int(count),
                }
            )

        return {
            "dataset_id": dataset_id,
            "column": column,
            "values": values,
        }

    def correlations(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        numeric_df = df.select_dtypes(
            include="number"
        )

        if len(numeric_df.columns) < 2:
            return {
                "dataset_id": dataset_id,
                "correlations": [],
            }

        matrix = numeric_df.corr()

        correlations = []

        columns = list(matrix.columns)

        for i, column_a in enumerate(columns):
            for column_b in columns[i + 1:]:

                value = matrix.loc[
                    column_a,
                    column_b,
                ]

                if pd.isna(value):
                    continue

                correlations.append(
                    {
                        "column_a": str(column_a),
                        "column_b": str(column_b),
                        "correlation": round(
                            float(value),
                            4,
                        ),
                    }
                )

        correlations.sort(
            key=lambda item: abs(
                item["correlation"]
            ),
            reverse=True,
        )

        return {
            "dataset_id": dataset_id,
            "correlations": correlations,
        }

    def group_by(
        self,
        dataset_id: str,
        group_column: str,
        value_column: str,
        aggregation: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        self._validate_column(
            df,
            group_column,
        )

        self._validate_column(
            df,
            value_column,
        )

        allowed_aggregations = {
            "sum",
            "mean",
            "median",
            "min",
            "max",
            "count",
        }

        if aggregation not in allowed_aggregations:
            raise ExplorationError(
                f"Unsupported aggregation '{aggregation}'."
            )

        if (
            aggregation != "count"
            and not pd.api.types.is_numeric_dtype(
                df[value_column]
            )
        ):
            raise ExplorationError(
                f"Column '{value_column}' must be numeric "
                f"for '{aggregation}'."
            )

        grouped = (
            df.groupby(
                group_column,
                dropna=False,
            )[value_column]
            .agg(aggregation)
            .reset_index()
        )

        results = []

        for _, row in grouped.iterrows():
            group_value = row[group_column]
            result_value = row[value_column]

            results.append(
                {
                    "group": (
                        None
                        if pd.isna(group_value)
                        else str(group_value)
                    ),
                    "value": self._serialise_value(
                        result_value
                    ),
                }
            )

        return {
            "dataset_id": dataset_id,
            "group_column": group_column,
            "value_column": value_column,
            "aggregation": aggregation,
            "results": results,
        }

    @staticmethod
    def _validate_column(
        df: pd.DataFrame,
        column: str,
    ) -> None:

        if column not in df.columns:
            raise ExplorationError(
                f"Column '{column}' does not exist."
            )

    @staticmethod
    def _number(
        value: Any,
    ) -> float | None:

        if pd.isna(value):
            return None

        return round(float(value), 4)

    @staticmethod
    def _serialise_value(
        value: Any,
    ) -> Any:

        if pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        # Handles NumPy numeric types.
        if hasattr(value, "item"):
            return value.item()

        return str(value)