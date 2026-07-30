import csv
from pathlib import Path
from typing import Any

import pandas as pd

from app.datasets.loader import DatasetLoader


class DatasetParser:
    """
    Inspects the structural integrity of uploaded datasets.

    The parser does NOT modify the raw dataset.
    """

    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def inspect(self, dataset_id: str) -> dict[str, Any]:
        metadata = self.loader.get_metadata(dataset_id)
        path = self.loader.get_path(
                                dataset_id,
                                stage="raw",
                            )

        file_type = metadata["file_type"]

        if file_type == "csv":
            return self._inspect_csv(dataset_id, path)

        if file_type == "xlsx":
            return self._inspect_excel(dataset_id, path)

        return {
            "dataset_id": dataset_id,
            "file_type": file_type,
            "parseable": False,
            "issues": [
                {
                    "type": "unsupported_file_type",
                    "message": f"Unsupported file type: {file_type}",
                }
            ],
        }

    def _inspect_csv(
        self,
        dataset_id: str,
        path: Path,
    ) -> dict[str, Any]:

        issues: list[dict[str, Any]] = []

        encoding = self._detect_encoding(path)

        if encoding is None:
            return {
                "dataset_id": dataset_id,
                "file_type": "csv",
                "parseable": False,
                "encoding": None,
                "delimiter": None,
                "columns_detected": None,
                "malformed_row_count": 0,
                "issues": [
                    {
                        "type": "encoding_error",
                        "message": "Unable to decode the CSV file.",
                    }
                ],
            }

        delimiter = self._detect_delimiter(path, encoding)

        if delimiter is None:
            return {
                "dataset_id": dataset_id,
                "file_type": "csv",
                "parseable": False,
                "encoding": encoding,
                "delimiter": None,
                "columns_detected": None,
                "malformed_row_count": 0,
                "issues": [
                    {
                        "type": "delimiter_detection_failed",
                        "message": "Unable to determine the CSV delimiter.",
                    }
                ],
            }

        malformed_rows = []
        columns_detected = None

        try:
            with path.open(
                "r",
                encoding=encoding,
                newline="",
            ) as file:

                reader = csv.reader(
                    file,
                    delimiter=delimiter,
                )

                header = next(reader, None)

                if header is None:
                    issues.append(
                        {
                            "type": "missing_header",
                            "message": "CSV file does not contain a header.",
                        }
                    )

                else:
                    columns_detected = len(header)

                    if columns_detected == 0:
                        issues.append(
                            {
                                "type": "empty_header",
                                "message": "CSV header is empty.",
                            }
                        )

                    for row_number, row in enumerate(
                        reader,
                        start=2,
                    ):
                        if len(row) != columns_detected:
                            malformed_rows.append(
                                {
                                    "row": row_number,
                                    "expected_fields": columns_detected,
                                    "actual_fields": len(row),
                                }
                            )

        except csv.Error as exc:
            issues.append(
                {
                    "type": "csv_structure_error",
                    "message": str(exc),
                }
            )

        for row in malformed_rows:
            issues.append(
                {
                    "type": "malformed_row",
                    "row": row["row"],
                    "expected_fields": row["expected_fields"],
                    "actual_fields": row["actual_fields"],
                    "message": (
                        f"Row {row['row']} contains "
                        f"{row['actual_fields']} fields; "
                        f"expected {row['expected_fields']}."
                    ),
                }
            )

        pandas_parseable = True

        try:
            pd.read_csv(
                path,
                encoding=encoding,
                sep=delimiter,
            )

        except Exception as exc:
            pandas_parseable = False

            issues.append(
                {
                    "type": "pandas_parse_error",
                    "message": str(exc),
                }
            )

        parseable = (
            pandas_parseable
            and len(malformed_rows) == 0
            and not any(
                issue["type"]
                in {
                    "missing_header",
                    "empty_header",
                    "csv_structure_error",
                }
                for issue in issues
            )
        )

        return {
            "dataset_id": dataset_id,
            "file_type": "csv",
            "parseable": parseable,
            "encoding": encoding,
            "delimiter": delimiter,
            "columns_detected": columns_detected,
            "malformed_row_count": len(malformed_rows),
            "issues": issues,
        }

    def _inspect_excel(
        self,
        dataset_id: str,
        path: Path,
    ) -> dict[str, Any]:

        issues: list[dict[str, Any]] = []

        try:
            excel_file = pd.ExcelFile(path)

            sheet_names = excel_file.sheet_names

            if not sheet_names:
                issues.append(
                    {
                        "type": "no_sheets",
                        "message": "Excel workbook contains no sheets.",
                    }
                )

                return {
                    "dataset_id": dataset_id,
                    "file_type": "xlsx",
                    "parseable": False,
                    "sheet_names": [],
                    "issues": issues,
                }

            return {
                "dataset_id": dataset_id,
                "file_type": "xlsx",
                "parseable": True,
                "sheet_names": sheet_names,
                "issues": [],
            }

        except Exception as exc:
            return {
                "dataset_id": dataset_id,
                "file_type": "xlsx",
                "parseable": False,
                "sheet_names": [],
                "issues": [
                    {
                        "type": "excel_parse_error",
                        "message": str(exc),
                    }
                ],
            }

    @staticmethod
    def _detect_encoding(path: Path) -> str | None:
        encodings = (
            "utf-8-sig",
            "utf-8",
            "cp1252",
            "latin-1",
        )

        for encoding in encodings:
            try:
                with path.open(
                    "r",
                    encoding=encoding,
                ) as file:
                    file.read()

                return encoding

            except UnicodeDecodeError:
                continue

        return None

    @staticmethod
    def _detect_delimiter(
        path: Path,
        encoding: str,
    ) -> str | None:

        try:
            with path.open(
                "r",
                encoding=encoding,
            ) as file:
                sample = file.read(8192)

            if not sample.strip():
                return None

            # First try Python's CSV sniffer.
            try:
                dialect = csv.Sniffer().sniff(
                    sample,
                    delimiters=",;\t|",
                )

                return dialect.delimiter

            except csv.Error:
                pass

            # Fallback:
            # inspect the header instead of giving up.
            first_line = sample.splitlines()[0]

            candidates = [",", ";", "\t", "|"]

            delimiter_counts = {
                delimiter: first_line.count(delimiter)
                for delimiter in candidates
            }

            best_delimiter = max(
                delimiter_counts,
                key=delimiter_counts.get,
            )

            if delimiter_counts[best_delimiter] == 0:
                return None

            return best_delimiter

        except (UnicodeDecodeError, OSError):
            return None