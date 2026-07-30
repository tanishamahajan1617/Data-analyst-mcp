import csv
from pathlib import Path
from typing import Any

from app.config import REPAIRED_DATA_DIR
from app.datasets.loader import DatasetLoader
from app.datasets.parser import DatasetParser


class StructuralRepairError(Exception):
    pass


class StructuralRepairEngine:
    def __init__(self) -> None:
        self.loader = DatasetLoader()
        self.parser = DatasetParser()

    def repair_csv_row(
        self,
        dataset_id: str,
        row_number: int,
        merge_into_column: str,
    ) -> dict[str, Any]:

        metadata = self.loader.get_metadata(dataset_id)

        if metadata["file_type"] != "csv":
            raise StructuralRepairError(
                "Row repair currently supports CSV files only."
            )

        inspection = self.parser.inspect(dataset_id)

        delimiter = inspection.get("delimiter")
        encoding = inspection.get("encoding")

        if not delimiter:
            raise StructuralRepairError(
                "Unable to determine dataset delimiter."
            )

        if not encoding:
            raise StructuralRepairError(
                "Unable to determine dataset encoding."
            )

        source_path = self.loader.get_path(
                                        dataset_id,
                                        stage="raw",
                                    )

        rows = self._read_rows(
            source_path,
            delimiter,
            encoding,
        )

        if not rows:
            raise StructuralRepairError(
                "Dataset is empty."
            )

        header = rows[0]

        if merge_into_column not in header:
            raise StructuralRepairError(
                f"Column '{merge_into_column}' does not exist."
            )

        if row_number < 2 or row_number > len(rows):
            raise StructuralRepairError(
                f"Row {row_number} does not exist."
            )

        target_row = rows[row_number - 1]

        expected_fields = len(header)
        actual_fields = len(target_row)

        if actual_fields <= expected_fields:
            raise StructuralRepairError(
                f"Row {row_number} does not contain extra fields."
            )

        target_index = header.index(merge_into_column)

        extra_count = actual_fields - expected_fields

        merge_end = target_index + extra_count + 1

        if merge_end > len(target_row):
            raise StructuralRepairError(
                "Unable to merge fields into the selected column."
            )

        values_to_merge = target_row[
            target_index:merge_end
        ]

        merged_value = delimiter.join(values_to_merge)

        repaired_row = (
            target_row[:target_index]
            + [merged_value]
            + target_row[merge_end:]
        )

        if len(repaired_row) != expected_fields:
            raise StructuralRepairError(
                "Repair did not produce the expected number of fields."
            )

        rows[row_number - 1] = repaired_row

        destination = self._get_repaired_path(
            dataset_id,
            metadata["filename"],
        )

        self._write_rows(
            destination,
            rows,
            delimiter,
            encoding,
        )

        return {
            "dataset_id": dataset_id,
            "status": "repaired",
            "row": row_number,
            "operation": "merge_extra_fields",
            "column": merge_into_column,
            "original_field_count": actual_fields,
            "repaired_field_count": len(repaired_row),
            "repaired_path": str(destination),
        }

    @staticmethod
    def _read_rows(
        path: Path,
        delimiter: str,
        encoding: str,
    ) -> list[list[str]]:

        with path.open(
            "r",
            encoding=encoding,
            newline="",
        ) as file:
            return list(
                csv.reader(
                    file,
                    delimiter=delimiter,
                )
            )

    @staticmethod
    def _write_rows(
        path: Path,
        rows: list[list[str]],
        delimiter: str,
        encoding: str,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding=encoding,
            newline="",
        ) as file:

            writer = csv.writer(
                file,
                delimiter=delimiter,
            )

            writer.writerows(rows)

    @staticmethod
    def _get_repaired_path(
        dataset_id: str,
        filename: str,
    ) -> Path:

        directory = (
            REPAIRED_DATA_DIR / dataset_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory / filename