import json
import shutil
from pathlib import Path
from typing import Any

from app.config import EXPORTS_DIR
from app.datasets.loader import DatasetLoader
from app.powerbi.semantic_model_builder import SemanticModelBuilder
from app.powerbi.pbir.report_builder import PBIRReportBuilder


class PowerBIProjectBuildError(Exception):
    pass


class PowerBIProjectBuilder:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]

        self.template_directory = (
            self.project_root
            / "power-bi-templates"
            / "base"
        )

        self.loader = DatasetLoader()
        self.semantic_model_builder = SemanticModelBuilder()
        self.pbir_report_builder = PBIRReportBuilder()

    def build(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        self._validate_template()

        # Also verifies that the dataset exists.
        self.loader.get_metadata(dataset_id)

        export_directory = (
            EXPORTS_DIR
            / dataset_id
            / "powerbi"
        )

        if export_directory.exists():
            shutil.rmtree(export_directory)

        export_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        template_pbip = (
            self.template_directory
            / "DataAnalystTemplate.pbip"
        )

        template_report = (
            self.template_directory
            / "DataAnalystTemplate.Report"
        )

        template_model = (
            self.template_directory
            / "DataAnalystTemplate.SemanticModel"
        )

        output_pbip = (
            export_directory
            / "DataAnalysis.pbip"
        )

        output_report = (
            export_directory
            / "DataAnalysis.Report"
        )

        output_model = (
            export_directory
            / "DataAnalysis.SemanticModel"
        )

        # --------------------------------------------------
        # 1. Copy Power BI template
        # --------------------------------------------------

        shutil.copytree(
            template_report,
            output_report,
        )

        shutil.copytree(
            template_model,
            output_model,
        )

        # --------------------------------------------------
        # 2. Create generated PBIP
        # --------------------------------------------------

        self._create_pbip(
            template_pbip=template_pbip,
            output_pbip=output_pbip,
        )

        # --------------------------------------------------
        # 3. Point report to generated semantic model
        # --------------------------------------------------

        self._update_report_model_reference(
            output_report
        )

        # --------------------------------------------------
        # 4. Export active dataset as controlled UTF-8 CSV
        # --------------------------------------------------

        data_directory = (
            export_directory
            / "data"
        )

        data_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        data_path = (
            data_directory
            / "data.csv"
        )

        df = self.loader.load(
            dataset_id
        )

        df.to_csv(
            data_path,
            index=False,
            encoding="utf-8",
        )

        # --------------------------------------------------
        # 5. Generate semantic model from dataset
        # --------------------------------------------------

        semantic_result = (
            self.semantic_model_builder.build(
                dataset_id=dataset_id,
                model_directory=output_model,
                data_path=data_path,
            )
        )

        # --------------------------------------------------
        # 6. Generate PBIR dashboard/report
        # --------------------------------------------------

        pbir_result = (
            self.pbir_report_builder.build(
                dataset_id=dataset_id,
                report_directory=output_report,
            )
        )

        # --------------------------------------------------
        # 7. Return generated project information
        # --------------------------------------------------

        return {
            "dataset_id": dataset_id,
            "status": "powerbi_project_created",
            "source_stage": (
                self.loader.get_active_stage(
                    dataset_id
                )
            ),
            "project_directory": str(
                export_directory
            ),
            "pbip_file": str(
                output_pbip
            ),
            "report_directory": str(
                output_report
            ),
            "semantic_model_directory": str(
                output_model
            ),
            "data_file": str(
                data_path
            ),
            "semantic_model": semantic_result,
            "pbir_report": pbir_result,
        }

    def _validate_template(self) -> None:

        required_paths = [
            (
                self.template_directory
                / "DataAnalystTemplate.pbip"
            ),
            (
                self.template_directory
                / "DataAnalystTemplate.Report"
            ),
            (
                self.template_directory
                / "DataAnalystTemplate.SemanticModel"
            ),
        ]

        missing = [
            str(path)
            for path in required_paths
            if not path.exists()
        ]

        if missing:
            raise PowerBIProjectBuildError(
                "Power BI template is incomplete. "
                f"Missing: {missing}"
            )

    @staticmethod
    def _create_pbip(
        template_pbip: Path,
        output_pbip: Path,
    ) -> None:

        try:
            with template_pbip.open(
                "r",
                encoding="utf-8-sig",
            ) as file:
                project = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise PowerBIProjectBuildError(
                "Could not read template PBIP file."
            ) from exc

        artifacts = project.get(
            "artifacts"
        )

        if not isinstance(
            artifacts,
            list,
        ):
            raise PowerBIProjectBuildError(
                "Template PBIP does not contain "
                "a valid artifacts list."
            )

        report_found = False

        for artifact in artifacts:

            report = artifact.get(
                "report"
            )

            if isinstance(
                report,
                dict,
            ):
                report["path"] = (
                    "DataAnalysis.Report"
                )

                report_found = True

        if not report_found:
            raise PowerBIProjectBuildError(
                "Could not find report artifact "
                "inside template PBIP."
            )

        try:
            with output_pbip.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    project,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except OSError as exc:
            raise PowerBIProjectBuildError(
                "Could not write generated PBIP file."
            ) from exc

    @staticmethod
    def _update_report_model_reference(
        report_directory: Path,
    ) -> None:

        definition_path = (
            report_directory
            / "definition.pbir"
        )

        if not definition_path.exists():
            raise PowerBIProjectBuildError(
                "Report definition.pbir "
                "was not found."
            )

        try:
            with definition_path.open(
                "r",
                encoding="utf-8-sig",
            ) as file:
                definition = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise PowerBIProjectBuildError(
                "Could not read report "
                "definition.pbir."
            ) from exc

        dataset_reference = (
            definition.get(
                "datasetReference"
            )
        )

        if not isinstance(
            dataset_reference,
            dict,
        ):
            raise PowerBIProjectBuildError(
                "Report does not contain "
                "datasetReference."
            )

        by_path = (
            dataset_reference.get(
                "byPath"
            )
        )

        if not isinstance(
            by_path,
            dict,
        ):
            raise PowerBIProjectBuildError(
                "Report does not use a "
                "byPath semantic model reference."
            )

        by_path["path"] = (
            "../DataAnalysis.SemanticModel"
        )

        try:
            with definition_path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    definition,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except OSError as exc:
            raise PowerBIProjectBuildError(
                "Could not update report "
                "semantic model reference."
            ) from exc