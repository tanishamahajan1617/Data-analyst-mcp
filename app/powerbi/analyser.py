from typing import Any
import re

import pandas as pd

from app.datasets.loader import DatasetLoader


class BIAnalyzer:
    """
    Performs lightweight structural analysis of a dataset
    for downstream BI planning.

    Classifies columns into:
    - numeric
    - categorical
    - datetime

    Datetime inference is deliberately conservative to
    avoid treating arbitrary text, identifiers, names,
    and numeric-looking strings as dates.
    """

    # Common date-like forms:
    # 2026-07-30
    # 30/07/2026
    # 07/30/2026
    # 30-07-2026
    # 2026/07/30
    # 30.07.2026
    _DATE_PATTERN = re.compile(
        r"^\s*(?:"
        r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
        r"|"
        r"\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"
        r")"
        r"(?:[ T].*)?"
        r"\s*$"
    )

    # Examples:
    # Jan 10 2026
    # January 10, 2026
    # 10 Jan 2026
    # 10 January 2026
    _MONTH_PATTERN = re.compile(
        r"\b(?:"
        r"jan(?:uary)?|"
        r"feb(?:ruary)?|"
        r"mar(?:ch)?|"
        r"apr(?:il)?|"
        r"may|"
        r"jun(?:e)?|"
        r"jul(?:y)?|"
        r"aug(?:ust)?|"
        r"sep(?:t(?:ember)?)?|"
        r"oct(?:ober)?|"
        r"nov(?:ember)?|"
        r"dec(?:ember)?"
        r")\b",
        re.IGNORECASE,
    )

    # Column-name hints are supporting evidence only.
    _DATETIME_NAME_HINTS = {
        "date",
        "datetime",
        "timestamp",
        "time",
        "created",
        "created_at",
        "updated",
        "updated_at",
        "modified",
        "modified_at",
        "start_date",
        "end_date",
        "order_date",
        "ship_date",
        "invoice_date",
        "transaction_date",
        "purchase_date",
        "sale_date",
        "birth_date",
        "dob",
    }

    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def analyze(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        df = self.loader.load(dataset_id)

        numeric_columns: list[str] = []
        categorical_columns: list[str] = []
        datetime_columns: list[str] = []

        for column in df.columns:
            column_name = str(column)
            series = df[column]

            # Already a real datetime dtype.
            if pd.api.types.is_datetime64_any_dtype(
                series
            ):
                datetime_columns.append(
                    column_name
                )
                continue

            # Numeric data should not be passed into
            # datetime inference. This also prevents
            # years/IDs/numeric codes being misclassified.
            if pd.api.types.is_numeric_dtype(
                series
            ):
                numeric_columns.append(
                    column_name
                )
                continue

            if self._looks_like_datetime(
                series=series,
                column_name=column_name,
            ):
                datetime_columns.append(
                    column_name
                )
                continue

            categorical_columns.append(
                column_name
            )

        return {
            "dataset_id": dataset_id,
            "stage": self.loader.get_active_stage(
                dataset_id
            ),
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "numeric_columns": numeric_columns,
            "categorical_columns": (
                categorical_columns
            ),
            "datetime_columns": datetime_columns,
        }

    @classmethod
    def _looks_like_datetime(
        cls,
        series: pd.Series,
        column_name: str = "",
    ) -> bool:
        """
        Determine whether a string/object column is
        genuinely likely to represent datetime values.

        The method first checks whether values have
        date-like structure. Pandas parsing is performed
        only after enough values pass that check.
        """

        if not (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            return False

        values = series.dropna()

        if values.empty:
            return False

        sample = (
            values.astype(str)
            .str.strip()
            .loc[lambda s: s != ""]
            .head(100)
        )

        if sample.empty:
            return False

        # ---------------------------------------------
        # 1. Reject obviously non-date-like text
        # ---------------------------------------------

        structural_matches = sample.map(
            cls._has_datetime_structure
        )

        structural_ratio = float(
            structural_matches.mean()
        )

        normalized_name = cls._normalize_column_name(
            column_name
        )

        name_suggests_datetime = (
            normalized_name
            in cls._DATETIME_NAME_HINTS
            or normalized_name.endswith("_date")
            or normalized_name.endswith("_datetime")
            or normalized_name.endswith("_timestamp")
        )

        # Without a useful column name, require strong
        # evidence from the actual values.
        if (
            structural_ratio < 0.8
            and not name_suggests_datetime
        ):
            return False

        # Even a date-like name should have at least
        # some date-like values before parsing.
        if (
            name_suggests_datetime
            and structural_ratio < 0.5
        ):
            return False

        # Parse only structurally plausible values.
        candidate_sample = sample[
            structural_matches
        ]

        if candidate_sample.empty:
            return False

        parsed = cls._parse_datetime_sample(
            candidate_sample
        )

        parse_success_ratio = float(
            parsed.notna().mean()
        )

        # Combine structural and parsing evidence.
        return (
            structural_ratio >= 0.8
            and parse_success_ratio >= 0.8
        )

    @classmethod
    def _has_datetime_structure(
        cls,
        value: str,
    ) -> bool:

        value = value.strip()

        if not value:
            return False

        if cls._DATE_PATTERN.match(value):
            return True

        if cls._MONTH_PATTERN.search(value):
            # Avoid accepting arbitrary text merely
            # because it contains a month word.
            return any(
                character.isdigit()
                for character in value
            )

        return False

    @staticmethod
    def _parse_datetime_sample(
        sample: pd.Series,
    ) -> pd.Series:
        """
        Parse plausible datetime values.

        format='mixed' lets pandas infer the format
        per value without producing the old
        'Could not infer format' warning.
        """

        try:
            return pd.to_datetime(
                sample,
                errors="coerce",
                format="mixed",
            )

        except (TypeError, ValueError):
            # Compatibility fallback for older pandas
            # versions without format='mixed'.
            return pd.to_datetime(
                sample,
                errors="coerce",
            )

    @staticmethod
    def _normalize_column_name(
        column_name: str,
    ) -> str:

        normalized = (
            column_name.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        return normalized