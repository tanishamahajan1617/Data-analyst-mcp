from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.datasets.store import DatasetStore, InvalidDatasetError
from app.schemas.dataset import DatasetUploadResponse
from app.analytics.profiler import DatasetProfiler
from app.analytics.quality import DataQualityAnalyzer
from app.datasets.parser import DatasetParser
from app.schemas.dataset import DatasetUploadResponse, StructuralRepairRequest
from app.datasets.repair import (
    StructuralRepairEngine,
    StructuralRepairError,
)
from app.analytics.cleaning.executor import (
    CleaningExecutionError,
    CleaningExecutor,
)
from app.analytics.explorer import (
    DatasetExplorer,
    ExplorationError,
)
from app.schemas.dataset import (
    CleaningExecutionRequest,
    DatasetUploadResponse,
    GroupByRequest,
    StructuralRepairRequest,
    ValueCountsRequest,
)
from app.datasets.loader import (
    DatasetLoader,
    DatasetNotFoundError,
    DatasetParseError,
    DatasetStageNotFoundError,
)
from app.powerbi.exporter import (
    PowerBIExporter,
    PowerBIExportError,
)
from app.powerbi.builder import (
    PowerBIProjectBuilder,
    PowerBIProjectBuildError,
)

from app.powerbi.dashboard_planner import DashboardLayoutPlanner
from app.analytics.cleaning.planner import CleaningPlanner
from app.powerbi.analyser import BIAnalyzer
from app.powerbi.semantic import SemanticAnalyzer
from app.powerbi.planner import DashboardPlanner

router = APIRouter(
    prefix="/api/v1/datasets",
    tags=["datasets"],
)

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
powerbi_exporter = PowerBIExporter()
powerbi_project_builder = PowerBIProjectBuilder()
dashboard_layout_planner = DashboardLayoutPlanner()


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

        return DatasetUploadResponse(**metadata)

    except InvalidDatasetError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{dataset_id}/profile")
def profile_dataset(dataset_id: str):
    try:
        return dataset_profiler.profile(dataset_id)

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


@router.get("/{dataset_id}/quality")
def analyze_dataset_quality(dataset_id: str):
    try:
        return data_quality_analyzer.analyze(dataset_id)

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
    
@router.get("/{dataset_id}/inspect")
def inspect_dataset(dataset_id: str):
    try:
        return dataset_parser.inspect(dataset_id)

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc        


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



@router.get("/{dataset_id}/status")
def get_dataset_status(dataset_id: str):
    try:
        metadata = dataset_loader.get_metadata(dataset_id)

        return {
            **metadata,
            "active_stage": DatasetLoader().get_active_stage(
                dataset_id
            ),
        }

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc       
@router.get("/{dataset_id}/cleaning-plan")
def create_cleaning_plan(dataset_id: str):
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


@router.get("/{dataset_id}/explore/summary")
def explore_summary(dataset_id: str):
    try:
        return dataset_explorer.summary(dataset_id)

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

@router.get("/{dataset_id}/explore/statistics")
def explore_statistics(dataset_id: str):
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
    
@router.get("/{dataset_id}/explore/correlations")
def explore_correlations(dataset_id: str):
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


@router.get("/{dataset_id}/bi/dashboard")
def get_dashboard_layout(
    dataset_id: str,
):
    return dashboard_layout_planner.create_layout(
        dataset_id
    )     

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


@router.post("/{dataset_id}/bi/build-project")
def build_powerbi_project(
    dataset_id: str,
):
    try:
        # Verify the dataset actually exists first.
        dataset_loader.get_metadata(dataset_id)

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