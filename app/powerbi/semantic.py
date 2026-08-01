from typing import Any

import pandas as pd

from app.datasets.loader import DatasetLoader
from app.powerbi.analyser import BIAnalyzer


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.loader = DatasetLoader()
        self.bi_analyzer = BIAnalyzer()

    def analyze(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        technical = self.bi_analyzer.analyze(
            dataset_id
        )

        datetime_columns = set(
            technical["datetime_columns"]
        )

        columns = []

        for column in df.columns:

            column_name = str(column)

            series = df[column]

            semantic_role = self._detect_role(
                column=column_name,
                series=series,
                datetime_columns=datetime_columns,
            )

            columns.append(
                {
                    "name": column_name,
                    "dtype": str(series.dtype),
                    "semantic_role": semantic_role,
                    "suggested_aggregation":
                        self._suggest_aggregation(
                            semantic_role,
                            column_name,
                        ),
                }
            )

        return {
            "dataset_id": dataset_id,
            "stage": self.loader.get_active_stage(
                dataset_id
            ),
            "columns": columns,
        }

    def _detect_role(
        self,
        column: str,
        series: pd.Series,
        datetime_columns: set[str],
    ) -> str:

        name = column.lower().strip()

        if column in datetime_columns:
            return "datetime"

        if self._is_identifier(name):
            return "identifier"

        if self._is_email(name):
            return "identifier"

        if self._is_percentage(name):
            return "percentage"

        if self._is_currency(name):
            return "currency"

        if self._looks_like_measure(
            name,
            series,
        ):
            return "measure"

        return "dimension"

    @staticmethod
    def _looks_like_measure(
        name: str,
        series: pd.Series,
    ) -> bool:

        if pd.api.types.is_numeric_dtype(series):
            return True

        measure_keywords = {
            "age",
            "score",
            "marks",
            "grade",
            "attendance",
            "study",
            "sleep",
            "screen",
            "exercise",
            "water",
            "hours",
            "duration",
            "time",
            "count",
            "quantity",
            "distance",
            "weight",
            "height",
            "salary",
            "income",
            "expense",
            "revenue",
            "sales",
            "profit",
            "cost",
            "price",
            "amount",
            "rating",
        }

        if any(
            keyword in name
            for keyword in measure_keywords
        ):
            return True

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        )

        if series.notna().sum() == 0:
            return False

        success_rate = (
            numeric.notna().sum()
            / series.notna().sum()
        )

        return success_rate >= 0.70

    @staticmethod
    def _is_identifier(
        name: str,
    ) -> bool:

        identifier_names = {
            "id",
            "user_id",
            "customer_id",
            "order_id",
            "product_id",
            "employee_id",
            "transaction_id",
            "student_id",
        }

        if name in identifier_names:
            return True

        return (
            name.endswith("_id")
            or name.endswith(" id")
        )

    @staticmethod
    def _is_email(
        name: str,
    ) -> bool:

        return (
            name == "email"
            or "email_address" in name
            or "email address" in name
        )

    @staticmethod
    def _is_currency(
        name: str,
    ) -> bool:

        keywords = {
            "salary",
            "revenue",
            "sales",
            "profit",
            "cost",
            "price",
            "amount",
            "income",
            "expense",
        }

        return any(
            keyword in name
            for keyword in keywords
        )

    @staticmethod
    def _is_percentage(
        name: str,
    ) -> bool:

        keywords = {
            "percentage",
            "percent",
            "margin",
            "rate",
            "ratio",
            "attendance_percent",
        }

        return any(
            keyword in name
            for keyword in keywords
        )

    @staticmethod
    def _suggest_aggregation(
        semantic_role: str,
        column: str,
    ) -> str | None:

        name = column.lower()

        if semantic_role == "identifier":
            return "distinct_count"

        if semantic_role == "datetime":
            return None

        if semantic_role == "dimension":
            return None

        if semantic_role == "percentage":
            return "average"

        if semantic_role == "currency":

            additive = {
                "sales",
                "revenue",
                "profit",
                "cost",
                "expense",
                "amount",
            }

            if any(
                keyword in name
                for keyword in additive
            ):
                return "sum"

            return "average"

        if semantic_role == "measure":

            average_keywords = {
                "age",
                "score",
                "marks",
                "grade",
                "attendance",
                "study",
                "sleep",
                "screen",
                "exercise",
                "water",
                "hours",
                "duration",
                "time",
                "rating",
                "height",
                "weight",
            }

            if any(
                keyword in name
                for keyword in average_keywords
            ):
                return "average"

            return "sum"

        return None