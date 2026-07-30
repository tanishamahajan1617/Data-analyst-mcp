import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    METADATA_DIR,
    RAW_DATA_DIR,
)


class InvalidDatasetError(Exception):
    pass


class DatasetStore:
    def _validate_extension(self, filename: str) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidDatasetError(
                "Unsupported file type. Only CSV and XLSX files are allowed."
            )

        return extension

    def save_path(
    self,
    source_path: Path,
    filename: str | None = None,
) -> dict:
        """
        Store a dataset from an existing local file.

        This is transport-independent and can be used by
        MCP, CLI, tests, or other application interfaces.
        """

        source_path = Path(source_path)

        if not source_path.exists():
            raise InvalidDatasetError(
                f"Dataset file does not exist: {source_path}"
            )

        if not source_path.is_file():
            raise InvalidDatasetError(
                "Dataset source must be a file."
            )

        safe_filename = Path(
            filename or source_path.name
        ).name

        extension = self._validate_extension(
            safe_filename
        )

        size_bytes = source_path.stat().st_size

        if size_bytes == 0:
            raise InvalidDatasetError(
                "Uploaded file is empty."
            )

        max_bytes = (
            MAX_FILE_SIZE_MB
            * 1024
            * 1024
        )

        if size_bytes > max_bytes:
            raise InvalidDatasetError(
                f"File exceeds the "
                f"{MAX_FILE_SIZE_MB} MB limit."
            )

        dataset_id = (
            f"ds_{uuid4().hex[:12]}"
        )

        dataset_directory = (
            RAW_DATA_DIR / dataset_id
        )

        dataset_directory.mkdir(
            parents=True,
            exist_ok=False,
        )

        destination = (
            dataset_directory
            / safe_filename
        )

        try:
            shutil.copy2(
                source_path,
                destination,
            )

            metadata = {
                "dataset_id": dataset_id,
                "filename": safe_filename,
                "file_type": (
                    extension.removeprefix(".")
                ),
                "size_bytes": size_bytes,
                "status": "uploaded",
                "uploaded_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            metadata_path = (
                METADATA_DIR
                / f"{dataset_id}.json"
            )

            with metadata_path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    metadata,
                    file,
                    indent=2,
                )

            return metadata

        except Exception:
            if dataset_directory.exists():
                shutil.rmtree(
                    dataset_directory
                )

            raise

    def save_content(
    self,
    filename: str,
    content: str,
) -> dict:
            """
            Store a dataset from text content.

            Intended primarily for CSV content received
            through remote MCP clients.
            """

            if not filename:
                raise InvalidDatasetError(
                    "Filename is required."
                )

            safe_filename = Path(filename).name

            extension = self._validate_extension(
                safe_filename
            )

            if extension != ".csv":
                raise InvalidDatasetError(
                    "Content upload currently supports CSV files only."
                )

            if not content:
                raise InvalidDatasetError(
                    "Dataset content is empty."
                )

            content_bytes = content.encode("utf-8")

            size_bytes = len(content_bytes)

            max_bytes = (
                MAX_FILE_SIZE_MB
                * 1024
                * 1024
            )

            if size_bytes > max_bytes:
                raise InvalidDatasetError(
                    f"File exceeds the "
                    f"{MAX_FILE_SIZE_MB} MB limit."
                )

            dataset_id = (
                f"ds_{uuid4().hex[:12]}"
            )

            dataset_directory = (
                RAW_DATA_DIR / dataset_id
            )

            dataset_directory.mkdir(
                parents=True,
                exist_ok=False,
            )

            destination = (
                dataset_directory
                / safe_filename
            )

            try:
                destination.write_bytes(
                    content_bytes
                )

                metadata = {
                    "dataset_id": dataset_id,
                    "filename": safe_filename,
                    "file_type": "csv",
                    "size_bytes": size_bytes,
                    "status": "uploaded",
                    "uploaded_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }

                metadata_path = (
                    METADATA_DIR
                    / f"{dataset_id}.json"
                )

                with metadata_path.open(
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        metadata,
                        file,
                        indent=2,
                    )

                return metadata

            except Exception:
                if dataset_directory.exists():
                    shutil.rmtree(
                        dataset_directory
                    )

                raise    