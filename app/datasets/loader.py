import json
from pathlib import Path
from typing import Literal

import pandas as pd

from app.config import (
    CLEANED_DATA_DIR,
    METADATA_DIR,
    RAW_DATA_DIR,
    REPAIRED_DATA_DIR,
)


DatasetStage = Literal[
    "auto",
    "raw",
    "repaired",
    "cleaned",
]


class DatasetNotFoundError(Exception):
    pass


class DatasetStageNotFoundError(Exception):
    pass


class DatasetParseError(Exception):
    pass


class DatasetLoader:
    def get_metadata(self, dataset_id: str) -> dict:
        metadata_path = METADATA_DIR / f"{dataset_id}.json"

        if not metadata_path.exists():
            raise DatasetNotFoundError(
                f"Dataset '{dataset_id}' does not exist."
            )

        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def get_path(
        self,
        dataset_id: str,
        stage: DatasetStage = "auto",
    ) -> Path:

        metadata = self.get_metadata(dataset_id)
        filename = metadata["filename"]

        paths = {
            "raw": RAW_DATA_DIR / dataset_id / filename,
            "repaired": REPAIRED_DATA_DIR / dataset_id / filename,
            "cleaned": CLEANED_DATA_DIR / dataset_id / filename,
        }

        if stage == "auto":
            for candidate_stage in (
                "cleaned",
                "repaired",
                "raw",
            ):
                candidate = paths[candidate_stage]

                if candidate.exists():
                    return candidate

            raise DatasetNotFoundError(
                f"No file exists for dataset '{dataset_id}'."
            )

        path = paths[stage]

        if not path.exists():
            raise DatasetStageNotFoundError(
                f"Dataset '{dataset_id}' has no "
                f"'{stage}' version."
            )

        return path

    def get_active_stage(
        self,
        dataset_id: str,
    ) -> str:

        metadata = self.get_metadata(dataset_id)
        filename = metadata["filename"]

        cleaned = CLEANED_DATA_DIR / dataset_id / filename
        repaired = REPAIRED_DATA_DIR / dataset_id / filename
        raw = RAW_DATA_DIR / dataset_id / filename

        if cleaned.exists():
            return "cleaned"

        if repaired.exists():
            return "repaired"

        if raw.exists():
            return "raw"

        raise DatasetNotFoundError(
            f"No file exists for dataset '{dataset_id}'."
        )

    def load(
        self,
        dataset_id: str,
        stage: DatasetStage = "auto",
    ) -> pd.DataFrame:

        metadata = self.get_metadata(dataset_id)
        path = self.get_path(dataset_id, stage)

        file_type = metadata["file_type"]

        try:
            if file_type == "csv":
                return pd.read_csv(path)

            if file_type == "xlsx":
                return pd.read_excel(path)

        except Exception as exc:
            raise DatasetParseError(
                f"Unable to parse dataset '{dataset_id}': {exc}"
            ) from exc

        raise DatasetParseError(
            f"Unsupported dataset type: {file_type}"
        )