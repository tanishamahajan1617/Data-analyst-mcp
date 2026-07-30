import json
import shutil
from pathlib import Path
from typing import Any

from app.powerbi.dashboard_planner import (
    DashboardLayoutPlanner,
)
from app.powerbi.pbir.visual_builder import (
    PBIRVisualBuilder,
)


class PBIRReportBuildError(Exception):
    pass


class PBIRReportBuilder:
    """
    Writes dashboard elements into an existing PBIR report.

    For now we intentionally support only the verified
    distinct-count Card visual.

    Other visual types will be added after we capture
    valid Power BI-generated reference definitions.
    """

    def __init__(self) -> None:
        self.layout_planner = DashboardLayoutPlanner()
        self.visual_builder = PBIRVisualBuilder()

    def build(
    self, 
    dataset_id: str,
    report_directory: Path,
) -> dict[str, Any]:

        report_directory = Path(report_directory)

        definition_directory = (
            report_directory
            / "definition"
        )

        pages_directory = (
            definition_directory
            / "pages"
        )

        pages_file = (
            pages_directory
            / "pages.json"
        )

        if not pages_file.exists():
            raise PBIRReportBuildError(
                "PBIR pages.json was not found."
            )

        # --------------------------------------------------
        # 1. Generate dashboard layout
        # --------------------------------------------------

        layout = self.layout_planner.create_layout(
            dataset_id
        )

        # --------------------------------------------------
        # 2. Find active report page
        # --------------------------------------------------

        page_name = self._get_active_page(
            pages_file
        )

        page_directory = (
            pages_directory
            / page_name
        )

        page_file = (
            page_directory
            / "page.json"
        )

        if not page_file.exists():
            raise PBIRReportBuildError(
                f"PBIR page was not found: {page_name}"
            )

        # --------------------------------------------------
        # 3. Update page metadata/layout
        # --------------------------------------------------

        self._update_page(
            page_file=page_file,
            layout=layout,
        )

        # --------------------------------------------------
        # 4. Prepare visuals directory
        # --------------------------------------------------

        visuals_directory = (
            page_directory
            / "visuals"
        )

        # Remove reference visuals copied from the
        # development template.
        if visuals_directory.exists():
            shutil.rmtree(
                visuals_directory
            )

        visuals_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------
        # 5. Generate supported PBIR visuals
        # --------------------------------------------------

        generated_visuals = []

        supported_types = {
            "card",
            "bar_chart",
            "column_chart",
            "slicer",
            "distribution_chart",
        }

        for element in layout["elements"]:

            element_type = element.get(
                "type"
            )

            # Ignore visual types that we have not
            # implemented yet.
            if element_type not in supported_types:
                continue

            aggregation = element.get(
                "aggregation"
            )

            # If the visual uses an aggregation,
            # ensure that aggregation is supported.
            if (
                aggregation
                and aggregation
                not in self.visual_builder.AGGREGATION_FUNCTIONS
            ):
                continue

            visual = self.visual_builder.build(
                element=element,
                tab_order=len(generated_visuals),
            )

            visual_id = visual["name"]

            visual_directory = (
                visuals_directory
                / visual_id
            )

            visual_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            visual_file = (
                visual_directory
                / "visual.json"
            )

            self._write_json(
                path=visual_file,
                data=visual,
            )

            generated_visuals.append(
                {
                    "name": visual_id,
                    "type": element_type,
                    "title": element.get(
                        "title"
                    ),
                    "path": str(
                        visual_file
                    ),
                }
            )

        # --------------------------------------------------
        # 6. Return report generation result
        # --------------------------------------------------

        return {
            "dataset_id": dataset_id,
            "page_name": page_name,
            "visual_count": len(
                generated_visuals
            ),
            "visuals": generated_visuals,
        }

    @staticmethod
    def _get_active_page(
        pages_file: Path,
    ) -> str:

        try:
            with pages_file.open(
                "r",
                encoding="utf-8-sig",
            ) as file:
                pages = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise PBIRReportBuildError(
                "Could not read pages.json."
            ) from exc

        page_name = pages.get(
            "activePageName"
        )

        if not page_name:
            page_order = pages.get(
                "pageOrder",
                [],
            )

            if page_order:
                page_name = page_order[0]

        if not page_name:
            raise PBIRReportBuildError(
                "PBIR report does not contain a page."
            )

        return page_name

    @staticmethod
    def _update_page(
        page_file: Path,
        layout: dict[str, Any],
    ) -> None:

        try:
            with page_file.open(
                "r",
                encoding="utf-8-sig",
            ) as file:
                page = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise PBIRReportBuildError(
                "Could not read page.json."
            ) from exc

        page_layout = layout["page"]

        page["displayName"] = page_layout[
            "display_name"
        ]

        page["width"] = page_layout[
            "width"
        ]

        page["height"] = page_layout[
            "height"
        ]

        PBIRReportBuilder._write_json(
            path=page_file,
            data=page,
        )

    @staticmethod
    def _write_json(
        path: Path,
        data: dict[str, Any],
    ) -> None:

        try:
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

        except OSError as exc:
            raise PBIRReportBuildError(
                f"Could not write PBIR file: {path}"
            ) from exc