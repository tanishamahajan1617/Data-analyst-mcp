import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import EXPORTS_DIR
from app.datasets.loader import DatasetLoader
from app.powerbi.planner import DashboardPlanner
from app.powerbi.semantic import SemanticAnalyzer


class PowerBIExportError(Exception):
    pass


class PowerBIExporter:
    def __init__(self) -> None:
        self.loader = DatasetLoader()
        self.semantic_analyzer = SemanticAnalyzer()
        self.dashboard_planner = DashboardPlanner()

    def export(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        metadata = self.loader.get_metadata(dataset_id)
        source_path = self.loader.get_path(dataset_id)

        active_stage = self.loader.get_active_stage(
            dataset_id
        )

        semantic_model = self.semantic_analyzer.analyze(
            dataset_id
        )

        dashboard_spec = self.dashboard_planner.create_plan(
            dataset_id
        )

        export_directory = (
            EXPORTS_DIR / dataset_id
        )

        export_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        data_path = self._export_data(
            source_path=source_path,
            export_directory=export_directory,
            file_type=metadata["file_type"],
        )

        semantic_path = (
            export_directory / "semantic_model.json"
        )

        dashboard_path = (
            export_directory / "dashboard_spec.json"
        )

        manifest_path = (
            export_directory / "manifest.json"
        )

        self._write_json(
            semantic_path,
            semantic_model,
        )

        self._write_json(
            dashboard_path,
            dashboard_spec,
        )

        manifest = {
            "dataset_id": dataset_id,
            "original_filename": metadata["filename"],
            "source_stage": active_stage,
            "exported_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "files": {
                "data": data_path.name,
                "semantic_model": semantic_path.name,
                "dashboard_spec": dashboard_path.name,
            },
        }

        self._write_json(
            manifest_path,
            manifest,
        )

        return {
            "dataset_id": dataset_id,
            "status": "exported",
            "source_stage": active_stage,
            "export_directory": str(export_directory),
            "files": {
                "data": str(data_path),
                "semantic_model": str(semantic_path),
                "dashboard_spec": str(dashboard_path),
                "manifest": str(manifest_path),
            },
        }

    @staticmethod
    def _export_data(
        source_path: Path,
        export_directory: Path,
        file_type: str,
    ) -> Path:

        if file_type == "csv":
            destination = export_directory / "data.csv"

        elif file_type == "xlsx":
            destination = export_directory / "data.xlsx"

        else:
            raise PowerBIExportError(
                f"Unsupported file type: {file_type}"
            )

        shutil.copy2(
            source_path,
            destination,
        )

        return destination

    @staticmethod
    def _write_json(
        path: Path,
        data: dict[str, Any],
    ) -> None:

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )