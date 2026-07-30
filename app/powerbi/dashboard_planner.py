from typing import Any

from app.powerbi.planner import DashboardPlanner


class DashboardLayoutError(Exception):
    pass


class DashboardLayoutPlanner:
    """
    Converts the logical dashboard plan into a layout specification.

    planner.py decides WHAT should be displayed.

    This class decides WHERE each dashboard element should be
    positioned on the Power BI report canvas.

    It does not generate PBIR JSON.
    """

    PAGE_WIDTH = 1280
    PAGE_HEIGHT = 720

    MARGIN = 24
    GAP = 16

    KPI_HEIGHT = 110
    SLICER_HEIGHT = 70

    def __init__(self) -> None:
        self.dashboard_planner = DashboardPlanner()

    def create_layout(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        plan = self.dashboard_planner.create_plan(
            dataset_id
        )

        kpis = plan.get("kpis", [])
        visuals = plan.get("visuals", [])
        slicers = plan.get("slicers", [])

        elements: list[dict[str, Any]] = []

        current_y = self.MARGIN

        # --------------------------------------------------
        # KPI ROW
        # --------------------------------------------------

        if kpis:
            kpi_elements = self._layout_kpis(
                kpis=kpis,
                y=current_y,
            )

            elements.extend(kpi_elements)

            current_y += (
                self.KPI_HEIGHT
                + self.GAP
            )

        # --------------------------------------------------
        # SLICER ROW
        # --------------------------------------------------

        if slicers:
            slicer_elements = self._layout_slicers(
                slicers=slicers,
                y=current_y,
            )

            elements.extend(slicer_elements)

            current_y += (
                self.SLICER_HEIGHT
                + self.GAP
            )

        # --------------------------------------------------
        # MAIN VISUAL AREA
        # --------------------------------------------------

        if visuals:
            visual_elements = self._layout_visuals(
                visuals=visuals,
                start_y=current_y,
            )

            elements.extend(visual_elements)

        return {
            "dataset_id": dataset_id,
            "title": plan["title"],
            "source_stage": plan["source_stage"],
            "page": {
                "name": "Overview",
                "display_name": "Overview",
                "width": self.PAGE_WIDTH,
                "height": self.PAGE_HEIGHT,
            },
            "elements": elements,
        }

    def _layout_kpis(
        self,
        kpis: list[dict[str, Any]],
        y: int,
    ) -> list[dict[str, Any]]:

        count = len(kpis)

        if count == 0:
            return []

        available_width = (
            self.PAGE_WIDTH
            - (2 * self.MARGIN)
            - ((count - 1) * self.GAP)
        )

        width = available_width // count

        elements = []

        for index, kpi in enumerate(kpis):
            x = (
                self.MARGIN
                + index * (width + self.GAP)
            )

            elements.append(
                self._create_element(
                    element=kpi,
                    x=x,
                    y=y,
                    width=width,
                    height=self.KPI_HEIGHT,
                )
            )

        return elements

    def _layout_slicers(
        self,
        slicers: list[dict[str, Any]],
        y: int,
    ) -> list[dict[str, Any]]:

        count = len(slicers)

        if count == 0:
            return []

        available_width = (
            self.PAGE_WIDTH
            - (2 * self.MARGIN)
            - ((count - 1) * self.GAP)
        )

        width = available_width // count

        elements = []

        for index, slicer in enumerate(slicers):
            x = (
                self.MARGIN
                + index * (width + self.GAP)
            )

            elements.append(
                self._create_element(
                    element=slicer,
                    x=x,
                    y=y,
                    width=width,
                    height=self.SLICER_HEIGHT,
                )
            )

        return elements

    def _layout_visuals(
        self,
        visuals: list[dict[str, Any]],
        start_y: int,
    ) -> list[dict[str, Any]]:

        if not visuals:
            return []

        available_width = (
            self.PAGE_WIDTH
            - (2 * self.MARGIN)
            - self.GAP
        )

        column_width = available_width // 2

        available_height = (
            self.PAGE_HEIGHT
            - start_y
            - self.MARGIN
        )

        row_count = (
            len(visuals) + 1
        ) // 2

        if row_count <= 0:
            return []

        total_gap_height = (
            (row_count - 1)
            * self.GAP
        )

        row_height = (
            available_height
            - total_gap_height
        ) // row_count

        # Prevent invalid/negative layouts.
        if row_height <= 0:
            raise DashboardLayoutError(
                "Dashboard contains too many visuals "
                "for the configured page height."
            )

        elements = []

        for index, visual in enumerate(visuals):

            row = index // 2
            column = index % 2

            x = (
                self.MARGIN
                + column
                * (column_width + self.GAP)
            )

            y = (
                start_y
                + row
                * (row_height + self.GAP)
            )

            elements.append(
                self._create_element(
                    element=visual,
                    x=x,
                    y=y,
                    width=column_width,
                    height=row_height,
                )
            )

        return elements

    @staticmethod
    def _create_element(
        element: dict[str, Any],
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:

        return {
            **element,
            "position": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            },
        }