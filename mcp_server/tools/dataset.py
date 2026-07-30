from pathlib import Path
from typing import Any

from app.datasets.loader import DatasetLoader
from app.datasets.parser import DatasetParser
from app.datasets.repair import StructuralRepairEngine
from app.datasets.store import DatasetStore
from app.datasets.remote import RemoteDatasetImporter


def register_dataset_tools(mcp) -> None:
    loader = DatasetLoader()
    parser = DatasetParser()
    repair_engine = StructuralRepairEngine()
    store = DatasetStore()
    remote_importer = RemoteDatasetImporter()


    @mcp.tool
    def import_dataset(
        file_path: str,
    ) -> dict[str, Any]:
        """
        Import a local CSV or XLSX file into the
        Data Analyst system.

        Returns a dataset_id that can be used by
        the other analysis and dashboard tools.
        """

        return store.save_path(
            source_path=Path(file_path),
        )

    @mcp.tool
    def import_dataset_from_url(
        url: str,
        filename: str | None = None,
    ) -> dict[str, Any]:
        """
        Import a CSV or XLSX dataset from a public HTTP
        or HTTPS URL.

        Use this tool when the MCP server is running
        remotely and the dataset is not available on
        the server's local filesystem.

        The URL must point directly to a downloadable
        CSV or XLSX file.

        Returns a dataset_id for use by the analysis,
        cleaning, and dashboard tools.
        """

        return remote_importer.import_url(
            url=url,
            filename=filename,
        )

    @mcp.tool
    def get_dataset_metadata(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Return stored metadata for an existing dataset.
        """

        metadata = loader.get_metadata(dataset_id)

        return {
            **metadata,
            "active_stage": loader.get_active_stage(
                dataset_id
            ),
        }

    @mcp.tool
    def inspect_dataset(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Inspect the raw dataset for structural problems.

        For CSV files this checks encoding, delimiter,
        malformed rows, headers, and parseability.

        For Excel files this checks workbook
        parseability and available sheets.
        """

        return parser.inspect(dataset_id)

    @mcp.tool
    def get_dataset_info(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Return basic information about the active
        version of a dataset.
        """

        metadata = loader.get_metadata(dataset_id)
        stage = loader.get_active_stage(dataset_id)
        path = loader.get_path(
            dataset_id,
            stage=stage,
        )

        df = loader.load(
            dataset_id,
            stage=stage,
        )

        return {
            "dataset_id": dataset_id,
            "filename": metadata["filename"],
            "file_type": metadata["file_type"],
            "active_stage": stage,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": [
                str(column)
                for column in df.columns
            ],
            "path": str(path),
        }

    @mcp.tool
    def repair_csv_row(
        dataset_id: str,
        row_number: int,
        merge_into_column: str,
    ) -> dict[str, Any]:
        """
        Repair a malformed CSV row containing extra
        fields by merging those fields into a selected
        column.

        Use inspect_dataset first to identify malformed
        rows before calling this tool.
        """

        return repair_engine.repair_csv_row(
            dataset_id=dataset_id,
            row_number=row_number,
            merge_into_column=merge_into_column,
        )