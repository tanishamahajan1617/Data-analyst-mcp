import shutil
from pathlib import Path
from typing import Any

from app.config import EXPORTS_DIR


class ArtifactNotFoundError(Exception):
    pass


class ArtifactService:

    def create_powerbi_archive(
        self,
        dataset_id: str,
        project_directory: str | Path,
    ) -> dict[str, Any]:

        project_path = Path(project_directory)

        if not project_path.exists():
            raise ArtifactNotFoundError(
                f"Power BI project does not exist: {project_path}"
            )

        artifact_directory = (
            EXPORTS_DIR
            / dataset_id
            / "artifacts"
        )

        artifact_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        archive_base = (
            artifact_directory
            / "powerbi_dashboard"
        )

        archive_path = Path(
            shutil.make_archive(
                base_name=str(archive_base),
                format="zip",
                root_dir=str(project_path),
            )
        )

        return {
            "artifact_id": dataset_id,
            "type": "powerbi_project",
            "filename": archive_path.name,
            "archive_path": str(archive_path),
            "size_bytes": archive_path.stat().st_size,
        }


    def get_powerbi_archive(
        self,
        dataset_id: str,
    ) -> Path:

        archive_path = (
            EXPORTS_DIR
            / dataset_id
            / "artifacts"
            / "powerbi_dashboard.zip"
        )

        if not archive_path.is_file():
            raise ArtifactNotFoundError(
                f"No Power BI artifact found for dataset {dataset_id}."
            )

        return archive_path