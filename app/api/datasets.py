import io

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.analytics.cleaning.executor import (
    CleaningExecutionError,
    CleaningExecutor,
)
from app.analytics.cleaning.planner import CleaningPlanner
from app.analytics.explorer import (
    DatasetExplorer,
    ExplorationError,
)
from app.analytics.profiler import DatasetProfiler
from app.analytics.quality import DataQualityAnalyzer

from app.datasets.loader import (
    DatasetLoader,
    DatasetNotFoundError,
    DatasetParseError,
    DatasetStageNotFoundError,
)
from app.datasets.parser import DatasetParser
from app.datasets.repair import (
    StructuralRepairEngine,
    StructuralRepairError,
)
from app.datasets.store import (
    DatasetStore,
    InvalidDatasetError,
)

from app.powerbi.analyser import BIAnalyzer
from app.powerbi.builder import (
    PowerBIProjectBuilder,
    PowerBIProjectBuildError,
)
from app.powerbi.dashboard_planner import (
    DashboardLayoutPlanner,
)
from app.powerbi.exporter import (
    PowerBIExporter,
    PowerBIExportError,
)
from app.powerbi.planner import DashboardPlanner
from app.powerbi.semantic import SemanticAnalyzer

from app.schemas.dataset import (
    CleaningExecutionRequest,
    DatasetUploadResponse,
    GroupByRequest,
    StructuralRepairRequest,
    ValueCountsRequest,
)


router = APIRouter(
    prefix="/api/v1/datasets",
    tags=["datasets"],
)


# ============================================================
# SERVICES
# ============================================================

dataset_store = DatasetStore()
dataset_profiler = DatasetProfiler()
data_quality_analyzer = DataQualityAnalyzer()
dataset_parser = DatasetParser()
dataset_loader = DatasetLoader()

structural_repair_engine = StructuralRepairEngine()

cleaning_planner = CleaningPlanner()
cleaning_executor = CleaningExecutor()

dataset_explorer = DatasetExplorer()

bi_analyzer = BIAnalyzer()
semantic_analyzer = SemanticAnalyzer()
dashboard_planner = DashboardPlanner()
dashboard_layout_planner = DashboardLayoutPlanner()

powerbi_exporter = PowerBIExporter()
powerbi_project_builder = PowerBIProjectBuilder()


# ============================================================
# DATASET UPLOAD
# ============================================================

@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_dataset(
    file: UploadFile = File(...),
) -> DatasetUploadResponse:

    try:

        metadata = dataset_store.save_upload(
            file
        )

        dataset_id = metadata["dataset_id"]

        df = dataset_loader.load(
            dataset_id
        )

        return DatasetUploadResponse(
            success=True,
            dataset_id=dataset_id,
            filename=metadata["filename"],
            file_type=metadata["file_type"],
            rows=int(len(df)),
            columns=int(len(df.columns)),
            status="ready",
        )

    except InvalidDatasetError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# PROFILE
# ============================================================

@router.get("/{dataset_id}/profile")
def profile_dataset(
    dataset_id: str,
):
    try:
        return dataset_profiler.profile(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# QUALITY
# ============================================================

@router.get("/{dataset_id}/quality")
def analyze_dataset_quality(
    dataset_id: str,
):
    try:
        return data_quality_analyzer.analyze(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ============================================================
# INSPECT
# ============================================================

@router.get("/{dataset_id}/inspect")
def inspect_dataset(
    dataset_id: str,
):
    try:
        return dataset_parser.inspect(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# STRUCTURAL REPAIR
# ============================================================

@router.post("/{dataset_id}/repair")
def repair_dataset_structure(
    dataset_id: str,
    request: StructuralRepairRequest,
):
    try:
        return structural_repair_engine.repair_csv_row(
            dataset_id=dataset_id,
            row_number=request.row_number,
            merge_into_column=request.merge_into_column,
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except StructuralRepairError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# STATUS
# ============================================================

@router.get("/{dataset_id}/status")
def get_dataset_status(
    dataset_id: str,
):
    try:
        metadata = dataset_loader.get_metadata(
            dataset_id
        )

        return {
            **metadata,
            "active_stage": (
                dataset_loader.get_active_stage(
                    dataset_id
                )
            ),
        }

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ============================================================
# POWER BI DATA SOURCE
# ============================================================

@router.get("/{dataset_id}/powerbi-data")
def get_powerbi_data(
    dataset_id: str,
):
    """
    Return the active dataset as UTF-8 CSV.

    Generated Power BI projects access this endpoint through
    Web.Contents instead of using a filesystem-specific
    File.Contents path.

    DatasetLoader resolves the active dataset stage, so if
    cleaning produced a cleaned active stage, Power BI gets
    that stage automatically.
    """

    try:
        # Verify that the dataset exists.
        dataset_loader.get_metadata(
            dataset_id
        )

        # Load the active stage.
        df = dataset_loader.load(
            dataset_id
        )

        csv_buffer = io.StringIO()

        df.to_csv(
            csv_buffer,
            index=False,
        )

        csv_bytes = (
            csv_buffer
            .getvalue()
            .encode("utf-8")
        )

        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'inline; filename="{dataset_id}.csv"'
                ),
                "Cache-Control": "no-store",
            },
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except (
        DatasetParseError,
        DatasetStageNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# CLEANING PLAN
# ============================================================

@router.get("/{dataset_id}/cleaning-plan")
def create_cleaning_plan(
    dataset_id: str,
):
    try:
        return cleaning_planner.create_plan(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# CLEAN DATASET
# ============================================================

@router.post("/{dataset_id}/clean")
def clean_dataset(
    dataset_id: str,
    request: CleaningExecutionRequest,
):
    try:
        operations = [
            operation.model_dump(
                exclude_none=True
            )
            for operation in request.operations
        ]

        return cleaning_executor.execute(
            dataset_id=dataset_id,
            operations=operations,
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except CleaningExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# EXPLORATION SUMMARY
# ============================================================

@router.get("/{dataset_id}/explore/summary")
def explore_summary(
    dataset_id: str,
):
    try:
        return dataset_explorer.summary(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# NUMERIC STATISTICS
# ============================================================

@router.get("/{dataset_id}/explore/statistics")
def explore_statistics(
    dataset_id: str,
):
    try:
        return dataset_explorer.numeric_statistics(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# CORRELATIONS
# ============================================================

@router.get("/{dataset_id}/explore/correlations")
def explore_correlations(
    dataset_id: str,
):
    try:
        return dataset_explorer.correlations(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# VALUE COUNTS
# ============================================================

@router.post("/{dataset_id}/explore/value-counts")
def explore_value_counts(
    dataset_id: str,
    request: ValueCountsRequest,
):
    try:
        return dataset_explorer.value_counts(
            dataset_id=dataset_id,
            column=request.column,
            limit=request.limit,
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except ExplorationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# GROUP BY
# ============================================================

@router.post("/{dataset_id}/explore/group-by")
def explore_group_by(
    dataset_id: str,
    request: GroupByRequest,
):
    try:
        return dataset_explorer.group_by(
            dataset_id=dataset_id,
            group_column=request.group_column,
            value_column=request.value_column,
            aggregation=request.aggregation,
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except ExplorationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# BI ANALYSIS
# ============================================================

@router.get("/{dataset_id}/bi/analyze")
def analyze_dataset_for_bi(
    dataset_id: str,
):
    try:
        return bi_analyzer.analyze(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# SEMANTIC ANALYSIS
# ============================================================

@router.get("/{dataset_id}/bi/semantic")
def analyze_dataset_semantics(
    dataset_id: str,
):
    try:
        return semantic_analyzer.analyze(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# DASHBOARD PLAN
# ============================================================

@router.get("/{dataset_id}/bi/dashboard-plan")
def create_dashboard_plan(
    dataset_id: str,
):
    try:
        return dashboard_planner.create_plan(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# ============================================================
# DASHBOARD LAYOUT
# ============================================================

@router.get("/{dataset_id}/bi/dashboard")
def get_dashboard_layout(
    dataset_id: str,
):
    return dashboard_layout_planner.create_layout(
        dataset_id
    )


# ============================================================
# POWER BI EXPORT
# ============================================================

@router.post("/{dataset_id}/bi/export")
def export_dataset_for_powerbi(
    dataset_id: str,
):
    try:
        return powerbi_exporter.export(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DatasetParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except PowerBIExportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# BUILD POWER BI PROJECT
# ============================================================

@router.post("/{dataset_id}/bi/build-project")
def build_powerbi_project(
    dataset_id: str,
):
    try:
        # Verify dataset exists before attempting project build.
        dataset_loader.get_metadata(
            dataset_id
        )

        return powerbi_project_builder.build(
            dataset_id
        )

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PowerBIProjectBuildError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc