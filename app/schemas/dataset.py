from pydantic import BaseModel
from typing import Any

from pydantic import BaseModel, Field

class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    file_type: str
    size_bytes: int
    status: str

class StructuralRepairRequest(BaseModel):
    row_number: int
    merge_into_column: str    

class CleaningOperation(BaseModel):
    type: str
    column: str | None = None
    new_name: str | None = None
    strategy: str | None = None
    value: Any | None = None
    errors: str | None = None


class CleaningExecutionRequest(BaseModel):
    operations: list[CleaningOperation] = Field(
        min_length=1
    )

class ValueCountsRequest(BaseModel):
    column: str
    limit: int = 10


class GroupByRequest(BaseModel):
    group_column: str
    value_column: str
    aggregation: str    
